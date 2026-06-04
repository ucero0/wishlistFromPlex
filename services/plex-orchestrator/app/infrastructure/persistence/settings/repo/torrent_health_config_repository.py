from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.torrent_health_config import (
    TorrentHealthConfig,
    TorrentHealthConfigUpdate,
)
from app.domain.ports.repositories.settings.torrent_health_config_repository_port import (
    TorrentHealthConfigRepositoryPort,
)
from app.infrastructure.persistence.settings.models.torrent_health_config_orm import (
    TORRENT_HEALTH_CONFIG_SINGLETON_ID,
    TorrentHealthConfigOrm,
)


class TorrentHealthConfigRepository(TorrentHealthConfigRepositoryPort):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_config(self) -> TorrentHealthConfig | None:
        orm = await self.session.get(
            TorrentHealthConfigOrm, TORRENT_HEALTH_CONFIG_SINGLETON_ID
        )
        return self._to_domain(orm) if orm else None

    async def insert_config(self, config: TorrentHealthConfig) -> TorrentHealthConfig:
        orm = TorrentHealthConfigOrm(
            id=TORRENT_HEALTH_CONFIG_SINGLETON_ID,
            grace_hours=config.grace_hours,
            min_availability=config.min_availability,
            unfinishable_active_minutes=config.unfinishable_active_minutes,
            no_complete_copy_days=config.no_complete_copy_days,
            stall_days=config.stall_days,
            skip_when_vpn_unhealthy=config.skip_when_vpn_unhealthy,
            use_strict_when_vpn_healthy=config.use_strict_when_vpn_healthy,
            strict_grace_hours=config.strict_grace_hours,
            strict_unfinishable_active_minutes=config.strict_unfinishable_active_minutes,
            strict_no_complete_copy_days=config.strict_no_complete_copy_days,
            strict_stall_days=config.strict_stall_days,
        )
        self.session.add(orm)
        await self.session.flush()
        await self.session.refresh(orm)
        return self._to_domain(orm)

    async def update_config(
        self, patch: TorrentHealthConfigUpdate
    ) -> TorrentHealthConfig:
        orm = await self.session.get(
            TorrentHealthConfigOrm, TORRENT_HEALTH_CONFIG_SINGLETON_ID
        )
        if orm is None:
            raise LookupError("torrent_health_config row is missing")
        for field, value in patch.model_dump(exclude_unset=True).items():
            setattr(orm, field, value)
        await self.session.flush()
        await self.session.refresh(orm)
        return self._to_domain(orm)

    def _to_domain(self, orm: TorrentHealthConfigOrm) -> TorrentHealthConfig:
        return TorrentHealthConfig(
            id=orm.id,
            grace_hours=orm.grace_hours,
            min_availability=orm.min_availability,
            unfinishable_active_minutes=orm.unfinishable_active_minutes,
            no_complete_copy_days=orm.no_complete_copy_days,
            stall_days=orm.stall_days,
            skip_when_vpn_unhealthy=orm.skip_when_vpn_unhealthy,
            use_strict_when_vpn_healthy=orm.use_strict_when_vpn_healthy,
            strict_grace_hours=orm.strict_grace_hours,
            strict_unfinishable_active_minutes=orm.strict_unfinishable_active_minutes,
            strict_no_complete_copy_days=orm.strict_no_complete_copy_days,
            strict_stall_days=orm.strict_stall_days,
            updated_at=orm.updated_at,
        )
