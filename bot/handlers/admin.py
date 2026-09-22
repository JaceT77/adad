import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from bot.bot import bot
from database import crud
from database.connection import async_session

logger = logging.getLogger(__name__)

router = Router(name="admin_router")


@router.message(Command("set_admin"))
async def cmd_set_admin(message: Message) -> None:
    """Displays a list of eligible users to promote to Administrator."""
    async with async_session() as session:
        caller = await crud.get_user_by_telegram_id(session, message.from_user.id)

        if not caller or not caller.is_admin:
            await message.answer("⛔ *Access Denied.*\nOnly administrators can use this command.")
            return

        candidates = await crud.get_non_admin_users(session)

        if not candidates:
            await message.answer(
                "ℹ️ *No eligible users found.*\nAll registered active users are already administrators."
            )
            return

        keyboard_buttons = []
        for user in candidates:
            role_label = user.role.value.replace("_", " ").title()
            handle = f" (@{user.username})" if user.username else ""
            button_text = f"👤 {user.full_name}{handle} — {role_label}"
            keyboard_buttons.append([InlineKeyboardButton(text=button_text, callback_data=f"promote:{user.id}")])

        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

        await message.answer(
            "👑 *Administrator Management*\n\n"
            "Select a specialist from the list below to promote them to *Administrator*:",
            reply_markup=keyboard,
        )


@router.callback_query(F.data.startswith("promote:"))
async def on_promote_user(callback: CallbackQuery) -> None:
    """Handles admin selection and notifies both parties."""
    target_user_id = int(callback.data.split(":")[1])

    async with async_session() as session:
        caller = await crud.get_user_by_telegram_id(session, callback.from_user.id)

        if not caller or not caller.is_admin:
            await callback.answer("⛔ Access denied: You are not an administrator.", show_alert=True)
            return

        target_user = await crud.set_user_admin(session, target_user_id, is_admin=True)

        if not target_user:
            await callback.answer("❌ User not found.", show_alert=True)
            return

    # 1. Confirmation message to the acting admin
    admin_confirm_text = (
        "✅ *Administrator Promoted Successfully!*\n\n"
        f"• *User:* `{target_user.full_name}`\n"
        f"• *Role:* `{target_user.role.value.replace('_', ' ').title()}`\n"
        f"• *Telegram ID:* `{target_user.telegram_id}`\n\n"
        "They now have full administrative privileges."
    )
    await callback.message.edit_text(admin_confirm_text)
    await callback.answer(f"{target_user.full_name} is now an admin!")

    # 2. Notification message to the newly promoted user
    try:
        user_notify_text = (
            "🎉 *Administrator Privileges Granted!*\n\n"
            f"You have been promoted to *Administrator* by *{caller.full_name}*.\n\n"
            "You can now use management tools:\n"
            "• `/admin` - View team status and admin dashboard\n"
            "• `/set_admin` - Promote other team members to admin"
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
    """Displays the management dashboard for administrators."""
    async with async_session() as session:
        caller = await crud.get_user_by_telegram_id(session, message.from_user.id)

        if not caller or not caller.is_admin:
            await message.answer("⛔ *Access Denied.*\nOnly administrators can access this dashboard.")
            return

        active_users = await crud.get_active_users(session)
        admins = [u for u in active_users if u.is_admin]
        specialists = [u for u in active_users if not u.is_admin]

    dashboard_text = (
        "👑 *Administrator Dashboard*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 *Total Active Members:* `{len(active_users)}`\n"
        f"🛡️ *Administrators:* `{len(admins)}`\n"
        f"👷 *Specialists:* `{len(specialists)}`\n\n"
        "📌 *Available Commands:*\n"
        "• `/set_admin` - Choose a specialist to promote to admin\n"
        "• `/profile` - View your personal profile & badge\n"
        "• `/task` - Submit a project task for overnight AI research\n"
    )
    await message.answer(dashboard_text)
