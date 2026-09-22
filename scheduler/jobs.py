import logging
from datetime import date

from aiogram import Bot

from bot.keyboards.inline import get_start_task_keyboard
from database import crud
from database.connection import async_session

logger = logging.getLogger(__name__)


async def evening_task_prompt_job(bot: Bot) -> None:
    """Har kuni soat 19:00da barcha faol mutaxassislarga ertangi kun vazifasi bo'yicha so'rov yuboradi."""
    logger.info("19:00 kechki rejalashtirish vazifasi ishga tushdi.")
    async with async_session() as session:
        users = await crud.get_active_users(session)

    prompt_text = (
        "🕖 *Xayrli kech!*\n\n"
        "Soat 19:00 bo'ldi — ertangi loyiha vazifasini kiritish vaqti keldi.\n"
        "Ertaga qaysi loyiha yoki bino ustida ishlaysiz?\n\n"
        "Vazifangizni hoziroq kiriting. AI tun bo'yi siz uchun *O'zbekiston SHNK normalari, mahalliy arzon materiallar, yashil texnologiyalar va AutoCAD andozasini* tayyorlab qo'yadi!"
    )

    for user in users:
        try:
            await bot.send_message(
                chat_id=user.telegram_id,
                text=prompt_text,
                reply_markup=get_start_task_keyboard(),
            )
            logger.info(f"19:00 so'rovi yuborildi: {user.telegram_id}")
        except Exception as e:
            logger.error(f"Foydalanuvchiga so'rov yuborishda xatolik ({user.telegram_id}): {e}")


async def morning_dossier_delivery_job(bot: Bot) -> None:
    """Har kuni soat 09:00da tayyor texnik ma'lumotnomani mutaxassisga yetkazadi."""
    today = date.today()
    logger.info(f"09:00 ertalabki ma'lumotnomalarni yetkazish vazifasi ishga tushdi: {today}.")

    async with async_session() as session:
        ready_tasks = await crud.get_ready_dossiers_for_delivery(session, target_date=today)

        for task in ready_tasks:
            if not task.dossier:
                continue

            user_telegram_id = task.user.telegram_id
            try:
                header = (
                    "🌅 *Xayrli tong! Bugungi ish kuningiz uchun tayyorlangan texnik ma'lumotnoma (shpargalka):*\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                )
                await bot.send_message(
                    chat_id=user_telegram_id,
                    text=header + task.dossier.full_content,
                )
                await crud.mark_task_delivered(session, task.id)
                logger.info(f"Ma'lumotnoma yetkazildi: vazifa {task.id}, foydalanuvchi {user_telegram_id}")
            except Exception as e:
                logger.error(f"Foydalanuvchiga yetkazishda xatolik ({user_telegram_id}): {e}")
