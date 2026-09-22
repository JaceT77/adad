import logging
from datetime import date

from aiogram import Bot

from bot.keyboards.inline import get_start_task_keyboard
from database import crud
from database.connection import async_session

logger = logging.getLogger(__name__)


async def evening_task_prompt_job(bot: Bot) -> None:
    """Runs at 19:00 daily: sends an interactive prompt to all active specialists."""
    logger.info("Executing 19:00 evening check-in job.")
    async with async_session() as session:
        users = await crud.get_active_users(session)

    prompt_text = (
        "🕖 *Good Evening!*\n\n"
        "It's 19:00 — time to set up your assignments for tomorrow.\n"
        "What project or building will you be working on?\n\n"
        "Submit your task now so the AI can prepare your *SHNK codes, local materials, green tech, and CAD templates* overnight!"
    )

    for user in users:
        try:
            await bot.send_message(
                chat_id=user.telegram_id,
                text=prompt_text,
                reply_markup=get_start_task_keyboard(),
            )
            logger.info(f"Evening prompt sent to user {user.telegram_id}")
        except Exception as e:
            logger.error(f"Failed to send evening prompt to user {user.telegram_id}: {e}")


async def morning_dossier_delivery_job(bot: Bot) -> None:
    """Runs at 09:00 daily: delivers pre-compiled dossiers to specialists."""
    today = date.today()
    logger.info(f"Executing 09:00 morning dossier delivery job for {today}.")

    async with async_session() as session:
        ready_tasks = await crud.get_ready_dossiers_for_delivery(session, target_date=today)

        for task in ready_tasks:
            if not task.dossier:
                continue

            user_telegram_id = task.user.telegram_id
            try:
                await bot.send_message(
                    chat_id=user_telegram_id,
                    text=task.dossier.full_content,
                )
                await crud.mark_task_delivered(session, task.id)
                logger.info(f"Delivered dossier for task {task.id} to user {user_telegram_id}")
            except Exception as e:
                logger.error(f"Failed to deliver dossier to user {user_telegram_id}: {e}")
