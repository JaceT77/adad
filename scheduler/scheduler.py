import logging

import pytz
from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from config.settings import settings
from scheduler.jobs import evening_task_prompt_job, morning_dossier_delivery_job

logger = logging.getLogger(__name__)


def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    tz = pytz.timezone(settings.TIMEZONE)
    scheduler = AsyncIOScheduler(timezone=tz)

    # 19:00 Evening Prompt Job
    scheduler.add_job(
        evening_task_prompt_job,
        trigger=CronTrigger(
            hour=settings.EVENING_CRON_HOUR,
            minute=settings.EVENING_CRON_MINUTE,
            timezone=tz,
        ),
        args=[bot],
        id="evening_task_prompt",
        replace_existing=True,
    )
    logger.info(
        f"Scheduled Evening Prompt at {settings.EVENING_CRON_HOUR:02d}:{settings.EVENING_CRON_MINUTE:02d} ({settings.TIMEZONE})"
    )

    # 09:00 Morning Delivery Job
    scheduler.add_job(
        morning_dossier_delivery_job,
        trigger=CronTrigger(
            hour=settings.MORNING_CRON_HOUR,
            minute=settings.MORNING_CRON_MINUTE,
            timezone=tz,
        ),
        args=[bot],
        id="morning_dossier_delivery",
        replace_existing=True,
    )
    logger.info(
        f"Scheduled Morning Delivery at {settings.MORNING_CRON_HOUR:02d}:{settings.MORNING_CRON_MINUTE:02d} ({settings.TIMEZONE})"
    )

    return scheduler
