"""Port for Plex server config persistence."""
from typing import Optional, Protocol

from app.domain.models.plex_server_config import PlexServerConfig


class PlexServerConfigRepositoryPort(Protocol):
    async def get_config(self) -> Optional[PlexServerConfig]:
        """Return the singleton server config row, if any."""
        ...

    async def upsert_admin_token(self, admin_token: str) -> PlexServerConfig:
        """Create or update the singleton admin token."""
        ...
