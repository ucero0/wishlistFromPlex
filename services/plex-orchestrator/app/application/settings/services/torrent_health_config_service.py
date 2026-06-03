"""Load and ensure torrent health policy from the database."""
from app.domain.models.torrent_health_config import (
    TorrentHealthConfig,
    TorrentHealthConfigUpdate,
)
from app.infrastructure.persistence.database import async_session_scope
from app.infrastructure.persistence.settings.repo.torrent_health_config_repository import (
    TorrentHealthConfigRepository,
)


class TorrentHealthConfigService:
    async def get_config(self) -> TorrentHealthConfig:
        async with async_session_scope() as session:
            repo = TorrentHealthConfigRepository(session)
            config = await repo.get_config()
            if config is not None:
                return config
            return await repo.insert_config(TorrentHealthConfig())

    async def ensure_config_row(self) -> TorrentHealthConfig:
        return await self.get_config()

    async def update_config(self, patch: TorrentHealthConfigUpdate) -> TorrentHealthConfig:
        if not patch.model_dump(exclude_unset=True):
            return await self.get_config()
        async with async_session_scope() as session:
            repo = TorrentHealthConfigRepository(session)
            if await repo.get_config() is None:
                await repo.insert_config(TorrentHealthConfig())
            return await repo.update_config(patch)


torrent_health_config_service = TorrentHealthConfigService()
