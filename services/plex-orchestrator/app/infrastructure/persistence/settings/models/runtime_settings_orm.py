from sqlalchemy import Column, DateTime, Float, Integer
from sqlalchemy.sql import func

from app.infrastructure.persistence.base import Base

RUNTIME_SETTINGS_SINGLETON_ID = 1


class RuntimeSettingsOrm(Base):
    __tablename__ = "runtime_settings"

    id = Column(Integer, primary_key=True, default=RUNTIME_SETTINGS_SINGLETON_ID)
    watchlist_download_interval_minutes = Column(Integer, nullable=False, default=60)
    ingest_poll_interval_minutes = Column(Integer, nullable=False, default=5)
    deferred_download_process_interval_minutes = Column(
        Integer, nullable=False, default=15
    )
    plex_library_paths_sync_interval_minutes = Column(
        Integer, nullable=False, default=360
    )
    tv_watchlist_ahead_episodes = Column(Integer, nullable=False, default=10)
    download_min_free_buffer_gb = Column(Float, nullable=False, default=10.0)
    download_default_required_gb = Column(Float, nullable=False, default=50.0)
    plex_library_disk_stats_max_age_hours = Column(Integer, nullable=False, default=6)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
