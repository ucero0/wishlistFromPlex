"""Scheduler service for managing background tasks."""
import logging
from typing import Callable, Awaitable
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)


class SchedulerService:
    """Service for managing scheduled background tasks."""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
    
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

