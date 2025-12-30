"""Factory for scheduler service."""
from app.infrastructure.scheduler.scheduler_service import SchedulerService
from app.infrastructure.scheduler.tasks import download_watch_list_media_task


def create_scheduler_service() -> SchedulerService:
    """
    Factory function to create SchedulerService with its dependencies.
    
    Returns:
        SchedulerService instance configured with all scheduled tasks
    """
    scheduler_service = SchedulerService()
    # Register tasks
    scheduler_service.register_download_watch_list_media_task(
        task_func=download_watch_list_media_task
    )
    return scheduler_service

