"""Query to get a single blacklist entry by Prowlarr GUID."""
from typing import Optional

from app.domain.models.blacklist_torrent import BlacklistTorrent
from app.domain.ports.repositories.blacklist_torrent.blacklist_torrent_repo import (
    BlacklistTorrentRepoPort,
)


class GetBlacklistTorrentByGuidQuery:
    """Get one blacklist entry by Prowlarr GUID."""

    def __init__(self, repo: BlacklistTorrentRepoPort):
        self._repo = repo

    async def execute(self, guid_prowlarr: str) -> Optional[BlacklistTorrent]:
        """Return the blacklist entry if found, else None."""
        return await self._repo.get_by_guid(guid_prowlarr)
