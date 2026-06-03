from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.runtime_settings import RuntimeSettings, RuntimeSettingsUpdate
from app.infrastructure.persistence.settings.models.runtime_settings_orm import (
    RUNTIME_SETTINGS_SINGLETON_ID,
    RuntimeSettingsOrm,
)


class RuntimeSettingsRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self) -> RuntimeSettings | None:
        orm = await self.session.get(RuntimeSettingsOrm, RUNTIME_SETTINGS_SINGLETON_ID)
        return self._to_domain(orm) if orm else None

    async def insert(self, settings: RuntimeSettings) -> RuntimeSettings:
        orm = RuntimeSettingsOrm(
            id=RUNTIME_SETTINGS_SINGLETON_ID,
            watchlist_download_interval_minutes=settings.watchlist_download_interval_minutes,
            ingest_poll_interval_minutes=settings.ingest_poll_interval_minutes,
            deferred_download_process_interval_minutes=settings.deferred_download_process_interval_minutes,
            plex_library_paths_sync_interval_minutes=settings.plex_library_paths_sync_interval_minutes,
            tv_watchlist_ahead_episodes=settings.tv_watchlist_ahead_episodes,
            download_min_free_buffer_gb=settings.download_min_free_buffer_gb,
            download_default_required_gb=settings.download_default_required_gb,
            plex_library_disk_stats_max_age_hours=settings.plex_library_disk_stats_max_age_hours,
        )
        self.session.add(orm)
        await self.session.flush()
        await self.session.refresh(orm)
        return self._to_domain(orm)

    async def update(self, patch: RuntimeSettingsUpdate) -> RuntimeSettings:
        orm = await self.session.get(RuntimeSettingsOrm, RUNTIME_SETTINGS_SINGLETON_ID)
        if orm is None:
            raise LookupError("runtime_settings row is missing")
        for field, value in patch.model_dump(exclude_unset=True).items():
            setattr(orm, field, value)
        await self.session.flush()
        await self.session.refresh(orm)
        return self._to_domain(orm)

    def _to_domain(self, orm: RuntimeSettingsOrm) -> RuntimeSettings:
        return RuntimeSettings(
            id=orm.id,
            watchlist_download_interval_minutes=orm.watchlist_download_interval_minutes,
            ingest_poll_interval_minutes=orm.ingest_poll_interval_minutes,
            deferred_download_process_interval_minutes=orm.deferred_download_process_interval_minutes,
            plex_library_paths_sync_interval_minutes=orm.plex_library_paths_sync_interval_minutes,
            tv_watchlist_ahead_episodes=orm.tv_watchlist_ahead_episodes,
            download_min_free_buffer_gb=orm.download_min_free_buffer_gb,
            download_default_required_gb=orm.download_default_required_gb,
            plex_library_disk_stats_max_age_hours=orm.plex_library_disk_stats_max_age_hours,
            updated_at=orm.updated_at,
        )
