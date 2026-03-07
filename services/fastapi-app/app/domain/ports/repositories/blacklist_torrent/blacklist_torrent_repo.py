"""Port for blacklist torrent repository."""
from typing import List, Optional, Protocol

from app.domain.models.blacklist_torrent import BlacklistTorrent


class BlacklistTorrentRepoPort(Protocol):
    """Repository for torrents blacklisted by Prowlarr GUID (e.g. infected, unhealthy)."""

    async def is_blacklisted(self, guid_prowlarr: str) -> bool:
        """Return True if the given Prowlarr GUID is on the blacklist."""
        ...

    async def add(self, blacklist_torrent: BlacklistTorrent) -> BlacklistTorrent:
        """Add a torrent to the blacklist. Idempotent per guid+reason or overwrite by guid."""
        ...

    async def get_all(self) -> List[BlacklistTorrent]:
        """Return all blacklist entries, ordered by created_at descending."""
        ...

    async def get_by_guid(self, guid_prowlarr: str) -> Optional[BlacklistTorrent]:
        """Get blacklist entry by Prowlarr GUID if any."""
        ...

    async def delete_by_guid(self, guid_prowlarr: str) -> bool:
        """Remove blacklist entry by GUID. Returns True if removed."""
        ...
