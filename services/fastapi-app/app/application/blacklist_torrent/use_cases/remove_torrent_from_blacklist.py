"""Use case: remove a torrent from the blacklist by Prowlarr GUID."""
from app.domain.ports.repositories.blacklist_torrent.blacklist_torrent_repo import (
    BlacklistTorrentRepoPort,
)


class RemoveTorrentFromBlacklistUseCase:
    """Remove a torrent (by Prowlarr GUID) from the blacklist."""

    def __init__(self, repo: BlacklistTorrentRepoPort):
        self._repo = repo

    async def execute(self, guid_prowlarr: str) -> bool:
        """Remove blacklist entry. Returns True if an entry was removed."""
        return await self._repo.delete_by_guid(guid_prowlarr)
