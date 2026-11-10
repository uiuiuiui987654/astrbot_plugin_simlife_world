"""Thin wrapper around APScheduler for the daily refresh and one-shot jobs."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable
from zoneinfo import ZoneInfo

from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.schedulers.asyncio import AsyncIOScheduler

DAILY_JOB_ID = "pvd:daily-generation"


class SchedulerRuntime:
    def __init__(self, timezone: ZoneInfo):
        self.scheduler = AsyncIOScheduler(
            timezone=timezone,
            executors={"default": AsyncIOExecutor()},
            job_defaults={"coalesce": True, "max_instances": 1, "misfire_grace_time": 120},
        )

    def start(self, generate_time: str, generate_callback: Callable[..., Any]) -> None:
        """Run ``generate_callback`` every day at ``HH:MM`` and start the scheduler."""
        hour, minute = (int(part) for part in generate_time.split(":"))
        self.scheduler.add_job(
            generate_callback, "cron", hour=hour, minute=minute, id=DAILY_JOB_ID, replace_existing=True
        )
        self.scheduler.start()

    def add_date_job(
        self, job_id: str, run_at: datetime, callback: Callable[..., Any], *args: Any, misfire_grace_time: int = 120
    ) -> None:
        self.scheduler.add_job(
            callback,
            "date",
            run_date=run_at,
            args=list(args),
            id=job_id,
            replace_existing=True,
            misfire_grace_time=max(1, misfire_grace_time),
        )

    def scheduled_jobs(self) -> list[tuple[str, datetime]]:
        """``(job id, next run)`` for every pending job, soonest first."""
        pending = [(job.id, job.next_run_time) for job in self.scheduler.get_jobs()]
        return sorted(((job_id, at) for job_id, at in pending if at is not None), key=lambda pair: (pair[1], pair[0]))

    def remove_prefix(self, prefix: str) -> None:
        for job in [job for job in self.scheduler.get_jobs() if job.id.startswith(prefix)]:
            job.remove()

    def remove(self, job_id: str) -> None:
        job = self.scheduler.get_job(job_id)
        if job is not None:
            job.remove()

    def stop(self) -> None:
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
