import uuid
from datetime import date, timedelta

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from bot.keyboards.inline import get_tier_keyboard
from bot.utils.sender import safe_send_message
from core.orchestrator import orchestrator
from database import crud
from database.connection import async_session

router = Router(name="evening_task_router")


class TaskSubmissionState(StatesGroup):
    waiting_for_project_title = State()
    waiting_for_building_type = State()
    waiting_for_notes = State()
    waiting_for_tier = State()


@router.callback_query(F.data == "action:submit_task")
async def callback_start_task(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.message.answer(
        "🏗️ <b>Ertangi Loyiha Vazifasini Kiritish</b>\n\n"
        "Iltimos, <b>loyiha nomini</b> kiriting:\n"
        "<i>(Masalan: 'Navoiy ko'chasidagi savdo markazi' yoki 'Yunusoboddagi 3 qavatli ofis binosi')</i>"
    )
    await state.set_state(TaskSubmissionState.waiting_for_project_title)
    await callback.answer()


@router.message(Command("task"))
async def cmd_task(message: Message, state: FSMContext) -> None:
    await message.answer(
        "🏗️ <b>Ertangi Loyiha Vazifasini Kiritish</b>\n\n"
        "Iltimos, <b>loyiha nomini</b> kiriting:\n"
        "<i>(Masalan: 'Navoiy ko'chasidagi savdo markazi' yoki 'Yunusoboddagi 3 qavatli ofis binosi')</i>"
    )
    await state.set_state(TaskSubmissionState.waiting_for_project_title)


@router.message(TaskSubmissionState.waiting_for_project_title)
async def process_project_title(message: Message, state: FSMContext) -> None:
    await state.update_data(project_title=message.text.strip())
    await message.answer(
        "🏢 <b>Bino turi (tipologiyasi)</b> qanday?\n\n"
        "<i>(Masalan: 'Tijorat ofisi', 'Turar-joy kotteji', 'Do'kon', 'Avtosalon', 'Ko'p qavatli bino')</i>"
    )
    await state.set_state(TaskSubmissionState.waiting_for_building_type)


@router.message(TaskSubmissionState.waiting_for_building_type)
async def process_building_type(message: Message, state: FSMContext) -> None:
    await state.update_data(building_type=message.text.strip())
    await message.answer(
        "📝 Iltimos, <b>qo'shimcha talab yoki e'tibor qaratilishi kerak bo'lgan jihatlarni</b> yozing:\n\n"
        "<i>(Masalan: 'O'zbekistonda arzon va sifatli devor materiallari, tualet uchun suvni qayta ishlash, va fasad uchun Toshkent dizayn kodiga e'tibor berilsin')</i>"
    )
    await state.set_state(TaskSubmissionState.waiting_for_notes)


@router.message(TaskSubmissionState.waiting_for_notes)
async def process_notes(message: Message, state: FSMContext) -> None:
    await state.update_data(raw_notes=message.text.strip())
    await message.answer(
        "🌍 <b>Qurilish standarti varianti:</b>\n"
        "Faqat O'zbekiston standartlari bo'yicha tayyorlansinmi yoki qo'shimcha Yevropa / Jahon ilg'or standarti ham kiritilsinmi?",
        reply_markup=get_tier_keyboard(),
    )
    await state.set_state(TaskSubmissionState.waiting_for_tier)


@router.callback_query(TaskSubmissionState.waiting_for_tier, F.data.startswith("tier:"))
async def process_tier_selection(callback: CallbackQuery, state: FSMContext) -> None:
    tier_choice = callback.data.split(":")[1]
    request_global_tier = tier_choice == "global"

    data = await state.get_data()
    project_title = data["project_title"]
    building_type = data["building_type"]
    raw_notes = data["raw_notes"]

    target_date = date.today() + timedelta(days=1)
    tier_label = (
        "O'zbekiston standarti + Jahon/Yevropa tajribasi" if request_global_tier else "O'zbekiston standarti (Asosiy)"
    )

    # 1. Tezkor javob va jarayon haqida bildirishnoma
    await callback.answer("Qabul qilindi! AI tahlilni boshlamoqda...")
    await callback.message.edit_text(
        "⏳ <b>Ma'lumotlar qabul qilindi!</b>\n\n"
        f"• <b>Loyiha:</b> <code>{project_title}</code>\n"
        f"• <b>Bino turi:</b> <code>{building_type}</code>\n"
        f"• <b>Standart:</b> <code>{tier_label}</code>\n\n"
        "🤖 <b>AI hozirda quyidagi yo'nalishlar bo'yicha chuqur tahlil olib bormoqda:</b>\n"
        "• ⚖️ O'zbekiston SHNK / QMQ qurilish me'yorlari va rasmiy manbalar\n"
        "• 🧱 Mahalliy zavod va bozorlardan arzon va sifatli materiallar\n"
        "• 🌿 Trilliant uslubidagi suvni qayta ishlash va quyosh energiyasi\n"
        "• 📐 AutoCAD (DWG) andozasi parametrlari\n\n"
        "⚡ <i>Biroz kuting, ma'lumotnoma (dossier) shakllantirilmoqda...</i>"
    )

    async with async_session() as session:
        user = await crud.get_or_create_user(
            session=session,
            telegram_id=callback.from_user.id,
            full_name=callback.from_user.full_name,
            username=callback.from_user.username,
        )

        task = await crud.create_daily_task(
            session=session,
            user_id=user.id,
            project_title=project_title,
            building_type=building_type,
            raw_notes=raw_notes,
            request_global_tier=request_global_tier,
            target_date=target_date,
        )

        # AI tadqiqotini bajarish
        await orchestrator.process_task(session=session, task=task)

    await state.clear()

    # 2. Tayyor bo'lgach, darhol ko'rish tugmasi bilan tasdiqlash
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⚡ Ma'lumotnomani hoziroq ko'rish",
                    callback_data=f"view_now:{task.id}",
                )
            ]
        ]
    )

    ready_text = (
        "✅ <b>Texnik ma'lumotnoma (Dossier) tayyor!</b>\n\n"
        f"• <b>Loyiha:</b> <code>{project_title}</code>\n"
        f"• <b>Bino turi:</b> <code>{building_type}</code>\n"
        f"• <b>Standart:</b> <code>{tier_label}</code>\n\n"
        "🕘 <b>Odatda ushbu ma'lumotnoma ertaga ertalab soat 09:00da yuboriladi.</b>\n"
        "Lekin 09:00 ni kutmasdan natijani hoziroq ko'rish uchun quyidagi tugmani bosing:"
    )
    await callback.message.edit_text(ready_text, reply_markup=keyboard)


@router.callback_query(F.data.startswith("view_now:"))
async def callback_view_now(callback: CallbackQuery) -> None:
    """Mutaxassisga tayyor ma'lumotnomani 09:00 ni kutmasdan hoziroq ko'rsatish."""
    task_id_str = callback.data.split(":")[1]
    task_id = uuid.UUID(task_id_str)

    async with async_session() as session:
        task = await crud.get_task_with_dossier(session, task_id)

    if not task or not task.dossier:
        await callback.answer("Ma'lumotnoma topilmadi.", show_alert=True)
        return

    await callback.answer("Ma'lumotnoma yuklanmoqda...")
    header = "⚡ <b>Siz so'ragan texnik ma'lumotnoma (Dossier):</b>\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    await safe_send_message(callback.bot, callback.message.chat.id, header + task.dossier.full_content)


@router.message(Command("instant_dossier"))
async def cmd_instant_dossier(message: Message) -> None:
    """Foydalanuvchining eng oxirgi tayyorlangan ma'lumotnomasini darhol chiqarish."""
    async with async_session() as session:
        user = await crud.get_user_by_telegram_id(session, message.from_user.id)
        if not user:
            await message.answer("Siz hali ro'yxatdan o'tmagansiz. Iltimos, <code>/start</code> bosing.")
            return

        task = await crud.get_latest_task_for_user(session, user.id)

    if not task or not task.dossier:
        await message.answer(
            "Sizda hali tayyorlangan ma'lumotnomalar mavjud emas. <code>/task</code> orqali yangi vazifa yuboring."
        )
        return

    header = "⚡ <b>Oxirgi tayyorlangan texnik ma'lumotnoma:</b>\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    await safe_send_message(message.bot, message.chat.id, header + task.dossier.full_content)


@router.message(Command("trigger_morning"))
async def cmd_trigger_morning(message: Message) -> None:
    """09:00 ertalabki yetkazish vazifasini hoziroq sinab ko'rish."""
    from bot.bot import bot
    from scheduler.jobs import morning_dossier_delivery_job

    await message.answer("🚀 09:00 ertalabki yetkazish vazifasi sinov tariqasida hoziroq ishga tushirildi...")
    await morning_dossier_delivery_job(bot)
    await message.answer("✅ Ertalabki ma'lumotnomalar tarqatildi!")


@router.message(Command("trigger_evening"))
async def cmd_trigger_evening(message: Message) -> None:
    """19:00 kechki so'rov vazifasini hoziroq sinab ko'rish."""
    from bot.bot import bot
    from scheduler.jobs import evening_task_prompt_job

    await message.answer("🚀 19:00 kechki so'rov vazifasi sinov tariqasida hoziroq ishga tushirildi...")
    await evening_task_prompt_job(bot)
