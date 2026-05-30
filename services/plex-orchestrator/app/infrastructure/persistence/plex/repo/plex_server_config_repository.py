"""Repository for Plex server config (singleton admin token)."""
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.plex_server_config import PlexServerConfig
from app.domain.ports.repositories.plex.plex_server_config_repository_port import (
    PlexServerConfigRepositoryPort,
)
from app.infrastructure.persistence.plex.models.plex_server_config_orm import (
    PLEX_SERVER_CONFIG_SINGLETON_ID,
    PlexServerConfigOrm,
)


class PlexServerConfigRepository(PlexServerConfigRepositoryPort):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_config(self) -> PlexServerConfig | None:
        orm = await self.session.get(PlexServerConfigOrm, PLEX_SERVER_CONFIG_SINGLETON_ID)
        return self._to_domain(orm) if orm else None

    async def upsert_admin_token(self, admin_token: str) -> PlexServerConfig:
        orm = await self.session.get(PlexServerConfigOrm, PLEX_SERVER_CONFIG_SINGLETON_ID)
        if orm is None:
            orm = PlexServerConfigOrm(
                id=PLEX_SERVER_CONFIG_SINGLETON_ID,
                admin_token=admin_token,
            )
            self.session.add(orm)
        else:
            orm.admin_token = admin_token
        await self.session.flush()
        await self.session.refresh(orm)
        return self._to_domain(orm)

    def _to_domain(self, orm: PlexServerConfigOrm) -> PlexServerConfig:
        return PlexServerConfig(
            id=orm.id,
            admin_token=orm.admin_token,
            created_at=orm.created_at,
            updated_at=orm.updated_at,
        )
