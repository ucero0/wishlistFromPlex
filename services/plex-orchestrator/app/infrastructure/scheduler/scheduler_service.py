"""Scheduler service for managing background tasks."""
import logging
from datetime import timezone
from typing import Any, Callable, Awaitable

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.application.pipelines.watchlist.models.watchlist_download_run_result import (
    SchedulerJobInfo,
)

logger = logging.getLogger(__name__)


class SchedulerService:
    """Service for managing scheduled background tasks."""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self._manual_runners: dict[str, Callable[[], Awaitable[Any]]] = {}
    
    def register_download_watch_list_media_task(
        self, 
        task_func: Callable[[], Awaitable[None]],
        interval_minutes: int = 10
    ):
        """
        Register the download watch list media task.
        
        Args:
            task_func: The async task function to execute
            interval_minutes: Interval in minutes between task executions (default: 10)
        """
        self.scheduler.add_job(
            task_func,
            trigger=IntervalTrigger(minutes=interval_minutes),
            id="download_watch_list_media",
            name="Download Watch List Media",
            replace_existing=True,
        )
        logger.info(f"Registered download watch list media task (interval: {interval_minutes} minutes)")

    def register_interval_task(
        self,
        task_func: Callable[[], Awaitable[None]],
        *,
        interval_minutes: int,
        job_id: str,
        name: str,
    ) -> None:
        """Register a generic async interval job."""
        self.scheduler.add_job(
            task_func,
            trigger=IntervalTrigger(minutes=interval_minutes),
            id=job_id,
            name=name,
            replace_existing=True,
        )
        logger.info("Registered %s (interval: %s minutes)", name, interval_minutes)

    def reschedule_interval(self, job_id: str, interval_minutes: int) -> None:
        """Update an existing interval job without restarting the application."""
        minutes = max(1, int(interval_minutes))
        self.scheduler.reschedule_job(
            job_id,
            trigger=IntervalTrigger(minutes=minutes),
        )
        logger.info("Rescheduled job %s to %s minutes", job_id, minutes)

    def register_manual_runner(
        self,
        job_id: str,
        runner: Callable[[], Awaitable[Any]],
    ) -> None:
        """Register a callable for on-demand job execution via the API."""
        self._manual_runners[job_id] = runner

    def list_jobs(self) -> list[SchedulerJobInfo]:
        jobs: list[SchedulerJobInfo] = []
        for job in self.scheduler.get_jobs():
            interval_minutes = None
            trigger = job.trigger
            if isinstance(trigger, IntervalTrigger):
                interval_minutes = int(trigger.interval.total_seconds() // 60)
            next_run = job.next_run_time
            jobs.append(
                SchedulerJobInfo(
                    id=job.id,
                    name=job.name or job.id,
                    interval_minutes=interval_minutes,
                    next_run_time=(
                        next_run.astimezone(timezone.utc).isoformat()
                        if next_run
                        else None
                    ),
                )
            )
        return sorted(jobs, key=lambda item: item.id)

    async def run_job_now(self, job_id: str) -> Any:
        runner = self._manual_runners.get(job_id)
        if runner is None:
            raise KeyError(job_id)
        return await runner()

    def start(self):
        """Start the scheduler."""
        logger.info("Starting scheduler service")
        self.scheduler.start()
        logger.info("Scheduler started")
    
    def shutdown(self):
        """Shutdown the scheduler gracefully."""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler stopped")
    
    @property
    def is_running(self) -> bool:
        """Check if scheduler is running."""
        return self.scheduler.running

