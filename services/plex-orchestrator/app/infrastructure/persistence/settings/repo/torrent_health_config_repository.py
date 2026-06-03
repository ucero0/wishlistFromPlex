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
            unfinishable_days=config.unfinishable_days,
            no_complete_copy_days=config.no_complete_copy_days,
            no_complete_zero_hours=config.no_complete_zero_hours,
            stall_days=config.stall_days,
            stall_no_peers_hours=config.stall_no_peers_hours,
            skip_when_vpn_unhealthy=config.skip_when_vpn_unhealthy,
            use_strict_when_vpn_healthy=config.use_strict_when_vpn_healthy,
            strict_grace_hours=config.strict_grace_hours,
            strict_unfinishable_days=config.strict_unfinishable_days,
            strict_no_complete_copy_days=config.strict_no_complete_copy_days,
            strict_no_complete_zero_hours=config.strict_no_complete_zero_hours,
            strict_stall_days=config.strict_stall_days,
            strict_stall_no_peers_hours=config.strict_stall_no_peers_hours,
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
            unfinishable_days=orm.unfinishable_days,
            no_complete_copy_days=orm.no_complete_copy_days,
            no_complete_zero_hours=orm.no_complete_zero_hours,
            stall_days=orm.stall_days,
            stall_no_peers_hours=orm.stall_no_peers_hours,
            skip_when_vpn_unhealthy=orm.skip_when_vpn_unhealthy,
            use_strict_when_vpn_healthy=orm.use_strict_when_vpn_healthy,
            strict_grace_hours=orm.strict_grace_hours,
            strict_unfinishable_days=orm.strict_unfinishable_days,
            strict_no_complete_copy_days=orm.strict_no_complete_copy_days,
            strict_no_complete_zero_hours=orm.strict_no_complete_zero_hours,
            strict_stall_days=orm.strict_stall_days,
            strict_stall_no_peers_hours=orm.strict_stall_no_peers_hours,
            updated_at=orm.updated_at,
        )
