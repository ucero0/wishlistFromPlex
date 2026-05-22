"""Whether this media is already downloading or waiting in the deferred queue."""
from __future__ import annotations

from typing import Literal, Optional

from app.domain.ports.repositories.deferredTorrent.deferredTorrentRepo import (
    DeferredTorrentRepoPort,
)
from app.domain.ports.repositories.torrentDownload.torrentDownloadRepo import (
    TorrentDownloadRepoPort,
)
from app.domain.services.media_identity import normalize_media_type_for_queue_match

MediaQueueReason = Literal[
    "already_downloading",
    "already_deferred",
    "same_torrent_in_deluge",
    "same_torrent_deferred",
    "same_media_identity_downloading",
    "same_media_identity_deferred",
]


class IsMediaAlreadyQueuedForDownloadQuery:
    """
    One Plex media item (``guid``) must not be sent to Deluge/deferred twice.

    Also blocks the same Prowlarr release or the same title/year/type when Plex
    guids differ across users.
    """

    def __init__(
        self,
        torrent_repo: TorrentDownloadRepoPort,
        deferred_repo: DeferredTorrentRepoPort,
    ):
        self._torrent_repo = torrent_repo
        self._deferred_repo = deferred_repo

    async def execute(
        self,
        guid_plex: str,
        *,
        guid_prowlarr: Optional[str] = None,
        title: Optional[str] = None,
        year: Optional[int] = None,
        media_type: Optional[str] = None,
    ) -> tuple[bool, Optional[MediaQueueReason]]:
        if await self._torrent_repo.is_guid_plex_downloading(guid_plex):
            return True, "already_downloading"
        if await self._deferred_repo.get_pending_by_guid_plex(guid_plex):
            return True, "already_deferred"

        if guid_prowlarr:
            if await self._torrent_repo.get_by_guid_prowlarr(guid_prowlarr):
                return True, "same_torrent_in_deluge"
            if await self._deferred_repo.get_pending_by_guid_prowlarr(guid_prowlarr):
                return True, "same_torrent_deferred"

        queue_type = normalize_media_type_for_queue_match(media_type)
        if title and queue_type:
            if await self._torrent_repo.has_by_media_identity(title, year, queue_type):
                return True, "same_media_identity_downloading"
            if await self._deferred_repo.get_pending_by_media_identity(
                title, year, queue_type
            ):
                return True, "same_media_identity_deferred"

        return False, None
