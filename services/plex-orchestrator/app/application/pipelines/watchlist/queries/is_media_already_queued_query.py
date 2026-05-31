"""Whether this media is already downloading or waiting in the deferred queue."""
from __future__ import annotations

from typing import Literal, Optional

from app.domain.ports.repositories.deferred_downloads.deferred_download_repository_port import (
    DeferredDownloadRepositoryPort,
)
from app.domain.ports.repositories.active_downloads.active_download_repository_port import (
    ActiveDownloadRepositoryPort,
)
from app.application.pipelines.watchlist.services.watchlist_search_builder import (
    watchlist_media_type,
)
from app.domain.models.media import MediaItem
from app.domain.services.media_identity import normalize_media_type_for_queue_match
from app.domain.services.media_library_guid import library_guid_for_media

MediaQueueReason = Literal[
    "already_downloading",
    "already_deferred",
    "same_torrent_in_deluge",
    "same_torrent_deferred",
    "same_media_identity_downloading",
    "same_media_identity_deferred",
]


class IsMediaAlreadyQueuedQuery:
    """
    One Plex media item (``guid``) must not be sent to Deluge/deferred twice.

    Also blocks the same Prowlarr release or the same title/year/type when Plex
    guids differ across users.
    """

    def __init__(
        self,
        torrent_repo: ActiveDownloadRepositoryPort,
        deferred_repo: DeferredDownloadRepositoryPort,
    ):
        self._torrent_repo = torrent_repo
        self._deferred_repo = deferred_repo

    async def execute_for_watchlist(
        self,
        watchlist: MediaItem,
        *,
        guid_prowlarr: Optional[str] = None,
    ) -> tuple[bool, Optional[MediaQueueReason]]:
        guids = {
            g
            for g in (
                watchlist.guid,
                watchlist.plex_library_guid,
                library_guid_for_media(watchlist),
            )
            if g
        }
        for guid in guids:
            queued, reason = await self.execute(
                guid,
                guid_prowlarr=guid_prowlarr,
                title=watchlist.title,
                year=watchlist.year,
                media_type=watchlist_media_type(watchlist),
            )
            if queued:
                return True, reason
        return False, None

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
