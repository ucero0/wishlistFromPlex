from typing import Protocol

from app.domain.models.torrent_health_config import (
    TorrentHealthConfig,
    TorrentHealthConfigUpdate,
)


class TorrentHealthConfigRepositoryPort(Protocol):
    async def get_config(self) -> TorrentHealthConfig | None:
        ...

    async def insert_config(self, config: TorrentHealthConfig) -> TorrentHealthConfig:
        ...

    async def update_config(
        self, patch: TorrentHealthConfigUpdate
    ) -> TorrentHealthConfig:
        ...
