from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, Message

from bot.keyboards.inline import get_role_keyboard, get_start_task_keyboard
from database import crud
from database.connection import async_session
from database.models import SpecialistRole

router = Router(name="start_router")


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
        "Welcome to the *AI Architectural Copilot*.\n\n"
        "This assistant helps specialists prepare daily project research dossiers:\n"
        "• 🕖 *19:00 Evening Check-in*: Ask for tomorrow's assignment.\n"
        "• 🤖 *Overnight AI Preparation*: Search Uzbek SHNK norms, materials, green tech, and CAD templates.\n"
        "• 🕘 *09:00 Morning Delivery*: Pre-compiled cheat sheet ready on your desk.\n\n"
        "Please select your engineering / design role below:"
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

    role_label = role.value.replace("_", " ").title()
    text = (
        f"✅ *Role updated:* `{role_label}`\n\n"
        "You will automatically receive daily reminders at *19:00* to set your next day's task.\n"
        "You can also submit a project task right now using the button below or `/task`."
    )
    await callback.message.edit_text(text, reply_markup=get_start_task_keyboard())
    await callback.answer("Role updated successfully!")


@router.message(Command("profile"))
async def cmd_profile(message: Message) -> None:
    async with async_session() as session:
        user = await crud.get_or_create_user(
            session=session,
            telegram_id=message.from_user.id,
            full_name=message.from_user.full_name,
            username=message.from_user.username,
        )

    role_label = user.role.value.replace("_", " ").title()
    text = (
        "👤 *Your Specialist Profile*\n"
        f"• *Name:* {user.full_name}\n"
        f"• *Role:* `{role_label}`\n"
        f"• *Status:* {'🟢 Active' if user.is_active else '🔴 Inactive'}\n"
        f"• *Reminders:* Evening 19:00 | Morning 09:00\n\n"
        "To change your role, tap below:"
    )
    await message.answer(text, reply_markup=get_role_keyboard())


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    help_text = (
        "📖 *AI Architectural Copilot Commands*\n\n"
        "• `/start` - Start onboarding and set your specialist role\n"
        "• `/task` - Submit tomorrow's project task for overnight research\n"
        "• `/profile` - View and update your profile & role\n"
        "• `/help` - Show this help message"
    )
    await message.answer(help_text)
