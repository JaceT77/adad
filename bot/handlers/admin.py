import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from bot.bot import bot
from database import crud
from database.connection import async_session
from database.models import SpecialistRole

logger = logging.getLogger(__name__)

router = Router(name="admin_router")

ROLE_NAMES_UZ = {
    SpecialistRole.ARCHITECT: "Arxitektor",
    SpecialistRole.STRUCTURAL_ENGINEER: "Konstruktor",
    SpecialistRole.COST_ESTIMATOR: "Smetachi",
    SpecialistRole.INTERIOR_DESIGNER: "Dizayner",
}


@router.message(Command("set_admin"))
async def cmd_set_admin(message: Message) -> None:
    """Administratorlikka tayinlash uchun mutaxassislar ro'yxatini ko'rsatadi."""
    async with async_session() as session:
        caller = await crud.get_user_by_telegram_id(session, message.from_user.id)

        if not caller or not caller.is_admin:
            await message.answer("⛔ *Ruxsat yo'q.*\nUshbu buyruqdan faqat administratorlar foydalana oladi.")
            return

        candidates = await crud.get_non_admin_users(session)

        if not candidates:
            await message.answer(
                "ℹ️ *Nomzodlar topilmadi.*\nBarcha faol mutaxassislar allaqachon administrator maqomiga ega."
            )
            return

        keyboard_buttons = []
        for user in candidates:
            role_label = ROLE_NAMES_UZ.get(user.role, user.role.value)
            handle = f" (@{user.username})" if user.username else ""
            button_text = f"👤 {user.full_name}{handle} — {role_label}"
            keyboard_buttons.append([InlineKeyboardButton(text=button_text, callback_data=f"promote:{user.id}")])

        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

        await message.answer(
            "👑 *Administrator Tayinlash*\n\nAdministratorlik huquqini bermoqchi bo'lgan mutaxassisni tanlang:",
            reply_markup=keyboard,
        )


@router.callback_query(F.data.startswith("promote:"))
async def on_promote_user(callback: CallbackQuery) -> None:
    """Tanlangan foydalanuvchini admin qiladi va ikkala tomonga xabar beradi."""
    target_user_id = int(callback.data.split(":")[1])

    async with async_session() as session:
        caller = await crud.get_user_by_telegram_id(session, callback.from_user.id)

        if not caller or not caller.is_admin:
            await callback.answer("⛔ Ruxsat yo'q: Siz administrator emassiz.", show_alert=True)
            return

        target_user = await crud.set_user_admin(session, target_user_id, is_admin=True)

        if not target_user:
            await callback.answer("❌ Mutaxassis topilmadi.", show_alert=True)
            return

    role_label = ROLE_NAMES_UZ.get(target_user.role, target_user.role.value)

    # 1. Amalni bajargan adminga tasdiqlash xabari
    admin_confirm_text = (
        "✅ *Administrator Muvaffaqiyatli Tayinlandi!*\n\n"
        f"• *Ism:* `{target_user.full_name}`\n"
        f"• *Mutaxassislik:* `{role_label}`\n"
        f"• *Telegram ID:* `{target_user.telegram_id}`\n\n"
        "Ushbu xodim endi to'liq administratorlik vakolatlariga ega."
    )
    await callback.message.edit_text(admin_confirm_text)
    await callback.answer(f"{target_user.full_name} endi admin!")

    # 2. Yangi tayinlangan adminga bildirishnoma xabari
    try:
        user_notify_text = (
            "🎉 *Tabriklaymiz, Sizga Administratorlik Huquqi Berildi!*\n\n"
            f"Siz *{caller.full_name}* tomonidan *Administrator* etib tayinlandingiz.\n\n"
            "Endi siz quyidagi boshqaruv buyruqlaridan foydalanishingiz mumkin:\n"
            "• `/admin` - Jamoa statistikasi va boshqaruv paneli\n"
            "• `/set_admin` - Boshqa mutaxassislarni ham admin etib tayinlash"
        )
        await bot.send_message(
            chat_id=target_user.telegram_id,
            text=user_notify_text,
        )
        logger.info(f"Admin promotion notification sent to user {target_user.telegram_id}")
    except Exception as e:
        logger.warning(f"Could not deliver notification to new admin {target_user.telegram_id}: {e}")


@router.message(Command("admin"))
async def cmd_admin_dashboard(message: Message) -> None:
    """Administratorlar uchun boshqaruv paneli."""
    async with async_session() as session:
        caller = await crud.get_user_by_telegram_id(session, message.from_user.id)

        if not caller or not caller.is_admin:
            await message.answer("⛔ *Ruxsat yo'q.*\nUshbu panel faqat administratorlar uchun.")
            return

        active_users = await crud.get_active_users(session)
        admins = [u for u in active_users if u.is_admin]
        specialists = [u for u in active_users if not u.is_admin]

    dashboard_text = (
        "👑 *Administrator Boshqaruv Paneli*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 *Jami faol a'zolar:* `{len(active_users)}`\n"
        f"🛡️ *Administratorlar:* `{len(admins)}`\n"
        f"👷 *Mutaxassislar:* `{len(specialists)}`\n\n"
        "📌 *Mavjud buyruqlar:*\n"
        "• `/set_admin` - Mutaxassisni Administrator etib tayinlash\n"
        "• `/profile` - Shaxsiy profilingiz va maqomingiz\n"
        "• `/task` - Ertangi loyiha topshirig'ini AI ga yuborish\n"
    )
    await message.answer(dashboard_text)
