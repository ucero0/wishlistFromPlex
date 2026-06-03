"""Operational settings in PostgreSQL. Defaults below; change via PUT /scheduler/settings."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RuntimeSettings(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = 1
    watchlist_download_interval_minutes: int = 60
    ingest_poll_interval_minutes: int = 5
    deferred_download_process_interval_minutes: int = 15
    plex_library_paths_sync_interval_minutes: int = 360
    tv_watchlist_ahead_episodes: int = 10
    download_min_free_buffer_gb: float = 10.0
    download_default_required_gb: float = 50.0
    plex_library_disk_stats_max_age_hours: int = 6
    updated_at: datetime | None = None


class RuntimeSettingsUpdate(BaseModel):
    watchlist_download_interval_minutes: int | None = Field(default=None, ge=1, le=10080)
    ingest_poll_interval_minutes: int | None = Field(default=None, ge=1, le=1440)
    deferred_download_process_interval_minutes: int | None = Field(
        default=None, ge=1, le=1440
    )
    plex_library_paths_sync_interval_minutes: int | None = Field(
        default=None, ge=1, le=10080
    )
    tv_watchlist_ahead_episodes: int | None = Field(default=None, ge=1, le=100)
    download_min_free_buffer_gb: float | None = Field(default=None, ge=0, le=1000)
    download_default_required_gb: float | None = Field(default=None, ge=1, le=2000)
    plex_library_disk_stats_max_age_hours: int | None = Field(
        default=None, ge=1, le=168
    )
