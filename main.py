import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from bot.bot import bot, dp
from bot.handlers import admin, evening, start
from config.settings import settings
from database.connection import init_db
from scheduler.scheduler import setup_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("adad_main")


async def main() -> None:
    logger.info("Starting AI Architectural Copilot Bot...")
    logger.info(f"Target Timezone: {settings.TIMEZONE}")
    logger.info(f"Evening Check-in: {settings.EVENING_CRON_HOUR:02d}:{settings.EVENING_CRON_MINUTE:02d}")
    logger.info(f"Morning Delivery: {settings.MORNING_CRON_HOUR:02d}:{settings.MORNING_CRON_MINUTE:02d}")

    # 1. Initialize Database Tables
    try:
        logger.info("Connecting to PostgreSQL and initializing schema...")
        await init_db()
        logger.info("Database schema initialized successfully.")
    except Exception as e:
        logger.error(
            f"Failed to connect to database: {e}\n"
            "Make sure PostgreSQL is running in Docker: `docker compose up -d postgres`"
        )
        sys.exit(1)

    # 2. Register Telegram Routers
    dp.include_router(start.router)
    dp.include_router(admin.router)
    dp.include_router(evening.router)

    # 3. Setup and Start Background Scheduler
    scheduler = setup_scheduler(bot)
    scheduler.start()
    logger.info("APScheduler started.")

    # 4. Start Bot Polling
    if "INITIAL_SETUP" in settings.BOT_TOKEN or "your_telegram" in settings.BOT_TOKEN:
        logger.warning(
            "\n" + "=" * 60 + "\n"
            "NOTICE: BOT_TOKEN is currently set to a setup placeholder.\n"
            "To connect your live Telegram bot:\n"
            "1. Create a bot with @BotFather on Telegram.\n"
            "2. Put your token in `.env` as `BOT_TOKEN=<your_token>`.\n"
            "3. Run `uv run python main.py` to start receiving real messages.\n" + "=" * 60
        )
        return

    try:
        logger.info("Bot polling started. Waiting for messages...")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Error during bot polling: {e}")
    finally:
        logger.info("Shutting down scheduler and bot...")
        scheduler.shutdown(wait=False)
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Application stopped gracefully.")
