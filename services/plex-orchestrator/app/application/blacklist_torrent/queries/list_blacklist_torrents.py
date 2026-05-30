"""Query to list all blacklisted torrents."""
from typing import List

from app.domain.models.blacklist_torrent import BlacklistTorrent
from app.domain.ports.repositories.blacklist_torrent.blacklist_torrent_repo import (
    BlacklistTorrentRepoPort,
)


class ListBlacklistTorrentsQuery:
    """List all blacklist entries (e.g. for API)."""

    def __init__(self, repo: BlacklistTorrentRepoPort):
        self._repo = repo

    async def execute(self) -> List[BlacklistTorrent]:
        """Return all blacklisted torrents, newest first."""
        return await self._repo.get_all()
