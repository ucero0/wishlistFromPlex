"""Use case: add a torrent to the blacklist (e.g. infected, unhealthy)."""
from typing import Optional

from app.domain.models.blacklist_torrent import BlacklistTorrent
from app.domain.ports.repositories.blacklist_torrent.blacklist_torrent_repo import (
    BlacklistTorrentRepoPort,
)


class AddTorrentToBlacklistUseCase:
    """Add a torrent (by Prowlarr GUID) to the blacklist with a reason and optional display info."""

    def __init__(self, repo: BlacklistTorrentRepoPort):
        self._repo = repo

    async def execute(
        self,
        guid_prowlarr: str,
        reason: str,
        name: Optional[str] = None,
        year: Optional[int] = None,
        media_type: Optional[str] = None,
    ) -> BlacklistTorrent:
        """
        Add or update blacklist entry for this GUID.
        reason: e.g. "infected", "unhealthy"
        name, year, media_type: optional display info (e.g. media title, year, movie/show).
        """
        entry = BlacklistTorrent(
            guid_prowlarr=guid_prowlarr,
            reason=reason,
            name=name,
            year=year,
            type=media_type,
        )
        return await self._repo.add(entry)
