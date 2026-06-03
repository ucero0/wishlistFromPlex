"""Load and apply runtime operational settings from PostgreSQL."""
import logging

from app.application.pipelines.watchlist.models.watchlist_download_run_result import (
    SchedulerJobInfo,
)
from app.domain.models.runtime_settings import RuntimeSettings, RuntimeSettingsUpdate
from app.infrastructure.persistence.database import async_session_scope
from app.infrastructure.persistence.settings.repo.runtime_settings_repository import (
    RuntimeSettingsRepository,
)
from app.infrastructure.scheduler.scheduler_service import SchedulerService

logger = logging.getLogger(__name__)

_SCHEDULER_INTERVAL_JOBS: tuple[tuple[str, str], ...] = (
    ("download_watch_list_media", "watchlist_download_interval_minutes"),
    ("sync_plex_library_paths", "plex_library_paths_sync_interval_minutes"),
    ("process_deferred_downloads", "deferred_download_process_interval_minutes"),
    ("process_deluge_torrents", "ingest_poll_interval_minutes"),
)


class RuntimeSettingsService:
    def __init__(self) -> None:
        self._cache: RuntimeSettings | None = None

    def get_cached(self) -> RuntimeSettings:
        if self._cache is None:
            raise RuntimeError(
                "Runtime settings cache is empty; call await ensure_loaded() at startup"
            )
        return self._cache

    async def get(self) -> RuntimeSettings:
        async with async_session_scope() as session:
            repo = RuntimeSettingsRepository(session)
            row = await repo.get()
            if row is None:
                row = await repo.insert(RuntimeSettings())
            self._cache = row
            return row

    async def ensure_loaded(self) -> RuntimeSettings:
        return await self.get()

    async def update(
        self, patch: RuntimeSettingsUpdate, *, scheduler: SchedulerService | None = None
    ) -> RuntimeSettings:
        async with async_session_scope() as session:
            repo = RuntimeSettingsRepository(session)
            if await repo.get() is None:
                await repo.insert(RuntimeSettings())
            row = await repo.update(patch)
        self._cache = row
        if scheduler is not None:
            self.apply_scheduler_intervals(scheduler, row)
        return row

    def apply_scheduler_intervals(
        self,
        scheduler: SchedulerService,
        config: RuntimeSettings | None = None,
    ) -> list[SchedulerJobInfo]:
        cfg = config or self.get_cached()
        for job_id, field_name in _SCHEDULER_INTERVAL_JOBS:
            minutes = getattr(cfg, field_name)
            scheduler.reschedule_interval(job_id, minutes)
            logger.info("Scheduler %s interval set to %s minutes", job_id, minutes)
        return scheduler.list_jobs()


runtime_settings_service = RuntimeSettingsService()
