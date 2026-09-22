from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, Message

from bot.keyboards.inline import get_role_keyboard, get_start_task_keyboard
from database import crud
from database.connection import async_session
from database.models import SpecialistRole

router = Router(name="start_router")

ROLE_NAMES_UZ = {
    SpecialistRole.ARCHITECT: "Arxitektor",
    SpecialistRole.STRUCTURAL_ENGINEER: "Konstruktor (Muhandis)",
    SpecialistRole.COST_ESTIMATOR: "Smetachi (Smetchik)",
    SpecialistRole.INTERIOR_DESIGNER: "Interyer va Fasad Dizayneri",
}


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    async with async_session() as session:
        user = await crud.get_or_create_user(
            session=session,
            telegram_id=message.from_user.id,
            full_name=message.from_user.full_name,
            username=message.from_user.username,
        )

    welcome_text = (
        f"👋 *Assalomu alaykum, {message.from_user.first_name}!*\n\n"
        "*Arxitektura va Qurilish bo'yicha AI Yordamchisiga* xush kelibsiz.\n\n"
        "Ushbu bot mutaxassislarga har kungi ishlarini rejalashtirish va tayyorgarlik ko'rishda yordam beradi:\n"
        "• 🕖 *19:00 Kechki so'rov*: Ertangi loyiha vazifasini kiritasiz.\n"
        "• 🤖 *AI tun bo'yi tayyorlaydi*: O'zbekiston SHNK/QMQ normalari, arzon va sifatli materiallar, yashil texnologiyalar va AutoCAD andozalarini izlab jamlaydi.\n"
        "• 🕘 *09:00 Ertalabki yetkazish*: Ishga kelganingizda to'liq texnik ma'lumotnoma (shpargalka) tayyor bo'ladi.\n\n"
        "Iltimos, o'z yo'nalishingiz / mutaxassisligingizni tanlang:"
    )
    await message.answer(welcome_text, reply_markup=get_role_keyboard())


@router.callback_query(F.data.startswith("role:"))
async def on_role_selected(callback: CallbackQuery) -> None:
    role_value = callback.data.split(":")[1]
    role = SpecialistRole(role_value)

    async with async_session() as session:
        await crud.update_user_role(
            session=session,
            telegram_id=callback.from_user.id,
            role=role,
        )

    role_label = ROLE_NAMES_UZ.get(role, role.value)
    text = (
        f"✅ *Mutaxassislik belgilandi:* `{role_label}`\n\n"
        "Endi har kuni soat *19:00*da ertangi vazifangizni kiritish uchun eslatma olasiz.\n"
        "Shuningdek, hoziroq loyiha topshirig'ini kiritish uchun pastdagi tugmani bosing yoki `/task` buyrug'idan foydalaning."
    )
    await callback.message.edit_text(text, reply_markup=get_start_task_keyboard())
    await callback.answer("Mutaxassislik muvaffaqiyatli saqlandi!")


@router.message(Command("profile"))
async def cmd_profile(message: Message) -> None:
    async with async_session() as session:
        user = await crud.get_or_create_user(
            session=session,
            telegram_id=message.from_user.id,
            full_name=message.from_user.full_name,
            username=message.from_user.username,
        )

    role_label = ROLE_NAMES_UZ.get(user.role, user.role.value)
    admin_badge = "👑 Administrator" if user.is_admin else "👷 Mutaxassis"
    text = (
        "👤 *Sizning Profilingiz*\n"
        f"• *Ism:* {user.full_name}\n"
        f"• *Maqom:* `{admin_badge}`\n"
        f"• *Mutaxassislik:* `{role_label}`\n"
        f"• *Holat:* {'🟢 Faol' if user.is_active else '🔴 Nofaol'}\n"
        f"• *Eslatmalar:* Kechqurun 19:00 | Ertalab 09:00\n\n"
        "Mutaxassislikni o'zgartirish uchun quyidan tanlang:"
    )
    await message.answer(text, reply_markup=get_role_keyboard())


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    async with async_session() as session:
        user = await crud.get_user_by_telegram_id(session, message.from_user.id)

    help_text = (
        "📖 *AI Yordamchi Buyruqlari*\n\n"
        "• `/start` - Botni ishga tushirish va mutaxassislikni tanlash\n"
        "• `/task` - Ertangi loyiha topshirig'ini AI ga yuborish\n"
        "• `/profile` - Profilingizni ko'rish va mutaxassislikni o'zgartirish\n"
    )
    if user and user.is_admin:
        help_text += (
            "\n👑 *Administrator Buyruqlari:*\n"
            "• `/admin` - Boshqaruv paneli va jamoa statistikasi\n"
            "• `/set_admin` - Mutaxassisni Administrator etib tayinlash\n"
        )
    help_text += "• `/help` - Ushbu yordam xabarini ko'rsatish"
    await message.answer(help_text)
