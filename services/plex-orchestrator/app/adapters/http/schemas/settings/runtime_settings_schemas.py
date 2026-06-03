from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.application.pipelines.watchlist.models.watchlist_download_run_result import (
    SchedulerJobInfo,
)
from app.domain.models.runtime_settings import RuntimeSettingsUpdate


class RuntimeSettingsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    watchlist_download_interval_minutes: int
    ingest_poll_interval_minutes: int
    deferred_download_process_interval_minutes: int
    plex_library_paths_sync_interval_minutes: int
    tv_watchlist_ahead_episodes: int
    download_min_free_buffer_gb: float
    download_default_required_gb: float
    plex_library_disk_stats_max_age_hours: int
    updated_at: datetime | None = None
    scheduler_jobs: list[SchedulerJobInfo] = []

    @classmethod
    def from_domain(cls, settings, *, scheduler_jobs=None) -> "RuntimeSettingsResponse":
        data = settings.model_dump()
        if scheduler_jobs is not None:
            data["scheduler_jobs"] = scheduler_jobs
        return cls.model_validate(data)


class UpdateRuntimeSettingsRequest(RuntimeSettingsUpdate):
    model_config = ConfigDict(extra="forbid")
