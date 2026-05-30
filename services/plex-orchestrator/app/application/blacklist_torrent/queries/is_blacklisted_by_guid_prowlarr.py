"""Query to check if a Prowlarr GUID is on the blacklist (do not send to Deluge)."""
from app.domain.ports.repositories.blacklist_torrent.blacklist_torrent_repo import (
    BlacklistTorrentRepoPort,
)


class IsBlacklistedByGuidProwlarrQuery:
    """Check if a torrent (by Prowlarr GUID) is blacklisted and should not be sent to Deluge."""

    def __init__(self, repo: BlacklistTorrentRepoPort):
        self._repo = repo

    async def execute(self, guid_prowlarr: str) -> bool:
        """Return True if the GUID is blacklisted (e.g. infected, unhealthy)."""
        return await self._repo.is_blacklisted(guid_prowlarr)
