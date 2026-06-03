"""Factory for scheduler service."""
from app.domain.models.runtime_settings import RuntimeSettings
from app.infrastructure.scheduler.scheduler_service import SchedulerService
from app.infrastructure.scheduler.tasks import (
    download_watch_list_media_task,
    process_deferred_downloads_task,
    process_deluge_torrents_task,
    register_scheduler_manual_runners,
    sync_plex_library_paths_task,
)


def create_scheduler_service() -> SchedulerService:
    """
    Register scheduled tasks using env/bootstrap defaults.

    Startup applies DB values via RuntimeSettingsService.apply_scheduler_intervals.
    """
    bootstrap = RuntimeSettings()
    scheduler_service = SchedulerService()
    scheduler_service.register_download_watch_list_media_task(
        task_func=download_watch_list_media_task,
        interval_minutes=max(1, bootstrap.watchlist_download_interval_minutes),
    )
    scheduler_service.register_interval_task(
        sync_plex_library_paths_task,
        interval_minutes=max(1, bootstrap.plex_library_paths_sync_interval_minutes),
        job_id="sync_plex_library_paths",
        name="Sync Plex Library Paths",
    )
    scheduler_service.register_interval_task(
        process_deferred_downloads_task,
        interval_minutes=max(
            1, bootstrap.deferred_download_process_interval_minutes
        ),
        job_id="process_deferred_downloads",
        name="Process Deferred Torrent Downloads",
    )
    scheduler_service.register_interval_task(
        process_deluge_torrents_task,
        interval_minutes=max(1, bootstrap.ingest_poll_interval_minutes),
        job_id="process_deluge_torrents",
        name="Deluge Ingest and Torrent Health",
    )
    register_scheduler_manual_runners(scheduler_service)
    return scheduler_service
