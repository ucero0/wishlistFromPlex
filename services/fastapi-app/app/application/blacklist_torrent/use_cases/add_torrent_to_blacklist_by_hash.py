"""Use case: add a torrent to the blacklist by its hash (uid). Looks up torrent download then adds by GUID."""
from typing import Optional

from app.domain.models.blacklist_torrent import BlacklistTorrent
from app.application.active_downloads.queries import GetActiveDownloadByUidQuery
from app.application.blacklist_torrent.use_cases import AddTorrentToBlacklistUseCase


class AddTorrentToBlacklistByHashUseCase:
    """Add a torrent to the blacklist by torrent hash (uid). Resolves GUID and optional display info from DB."""

    def __init__(
        self,
        get_active_download_by_uid: GetActiveDownloadByUidQuery,
        add_torrent_to_blacklist: AddTorrentToBlacklistUseCase,
    ):
        self._get_active_download = get_active_download_by_uid
        self._add_to_blacklist = add_torrent_to_blacklist

    async def execute(self, torrent_hash: str, reason: str) -> Optional[BlacklistTorrent]:
        """
        Look up torrent download by hash (uid); if found, add to blacklist with reason and its title/year/type.
        Returns the blacklist entry if added, None if no torrent download found for the hash.
        """
        torrent_download = await self._get_active_download.execute(torrent_hash)
        if not torrent_download:
            return None
        return await self._add_to_blacklist.execute(
            torrent_download.prowlarr_guid,
            reason,
            name=torrent_download.title,
            year=torrent_download.year,
            media_type=torrent_download.type,
        )
