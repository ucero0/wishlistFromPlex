"""Factory for scheduler service."""
from app.core.config import settings
from app.infrastructure.scheduler.scheduler_service import SchedulerService
from app.infrastructure.scheduler.tasks import (
    download_watch_list_media_task,
    process_deferred_downloads_task,
    sync_plex_library_paths_task,
)


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
    paths_interval_minutes = max(1, settings.plex_library_paths_sync_interval_hours * 60)
    scheduler_service.register_interval_task(
        sync_plex_library_paths_task,
        interval_minutes=paths_interval_minutes,
        job_id="sync_plex_library_paths",
        name="Sync Plex Library Paths",
    )
    deferred_interval = max(1, settings.deferred_download_process_interval_minutes)
    scheduler_service.register_interval_task(
        process_deferred_downloads_task,
        interval_minutes=deferred_interval,
        job_id="process_deferred_downloads",
        name="Process Deferred Torrent Downloads",
    )
    return scheduler_service

