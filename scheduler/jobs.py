import logging
from datetime import date

from aiogram import Bot

from bot.keyboards.inline import get_start_task_keyboard
from bot.utils.sender import safe_send_message
from database import crud
from database.connection import async_session

logger = logging.getLogger(__name__)


async def evening_task_prompt_job(bot: Bot) -> None:
    """Har kuni soat 19:00da barcha faol mutaxassislarga ertangi kun vazifasi bo'yicha so'rov yuboradi."""
    logger.info("19:00 kechki rejalashtirish vazifasi ishga tushdi.")
    async with async_session() as session:
        users = await crud.get_active_users(session)

    prompt_text = (
        "🕖 <b>Xayrli kech!</b>\n\n"
        "Soat 19:00 bo'ldi — ertangi loyiha vazifasini kiritish vaqti keldi.\n"
        "Ertaga qaysi loyiha yoki bino ustida ishlaysiz?\n\n"
        "Vazifangizni hoziroq kiriting. AI tun bo'yi siz uchun <b>O'zbekiston SHNK/QMQ me'yorlari, rasmiy manbalar, arzon mahalliy materiallar, yashil texnologiyalar va AutoCAD andozasini</b> tayyorlab qo'yadi!"
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
                    "🌅 <b>Xayrli tong! Bugungi ish kuningiz uchun tayyorlangan texnik ma'lumotnoma (shpargalka):</b>\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                )
                await safe_send_message(bot, user_telegram_id, header + task.dossier.full_content)
                await crud.mark_task_delivered(session, task.id)
                logger.info(f"Ma'lumotnoma yetkazildi: vazifa {task.id}, foydalanuvchi {user_telegram_id}")
            except Exception as e:
                logger.error(f"Foydalanuvchiga yetkazishda xatolik ({user_telegram_id}): {e}")
