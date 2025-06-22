"""APScheduler runner configuring periodic jobs."""

from __future__ import annotations

import os

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from providers.registry import ProviderRegistry

from .jobs import pull_and_sync_models

cron_expr = os.getenv("REFRESH_CRON", "0 0 * * *")
scheduler = AsyncIOScheduler()


def configure() -> None:
    registry = ProviderRegistry()
    trigger = CronTrigger.from_crontab(cron_expr)
    scheduler.add_job(
        pull_and_sync_models,
        trigger,
        kwargs={"registry": registry},
    )
