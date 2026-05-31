"""Persist a torrent for later Prowlarr/Deluge send when download volume has space."""
import logging

from app.domain.models.deferred_download import DeferredDownload
from app.domain.models.torrent_search import TorrentSearchResult
from app.domain.models.watchlist_item_for_user import WatchlistItemForUser
from app.domain.ports.repositories.deferred_downloads.deferred_download_repository_port import (
    DeferredDownloadRepositoryPort,
)
from app.domain.services.download_volume_space_checker import DownloadVolumeSpaceChecker
from app.domain.services.media_identity import normalize_media_type_for_queue_match
from app.domain.services.watchlist_download_tracking import deferred_download_from_watchlist

logger = logging.getLogger(__name__)


class EnqueueDeferredDownloadUseCase:
    def __init__(
        self,
        deferred_repo: DeferredDownloadRepositoryPort,
        space_checker: DownloadVolumeSpaceChecker,
    ):
        self._deferred_repo = deferred_repo
        self._space_checker = space_checker

    async def execute(
        self,
        *,
        entry: WatchlistItemForUser,
        torrent_result: TorrentSearchResult,
        search_query: str,
    ) -> DeferredDownload:
        watchlist = entry.item
        reason = self._space_checker.defer_reason_for_torrent(torrent_result.size)
        item = deferred_download_from_watchlist(
            entry,
            guid_prowlarr=torrent_result.guid or "",
            indexer_id=torrent_result.indexerId or 0,
            torrent_title=torrent_result.title,
            search_query=search_query,
            size_bytes=torrent_result.size,
            magnet_url=torrent_result.magnetUrl,
            defer_reason=reason or "deferred",
        )
        saved = await self._deferred_repo.upsert_pending(item)
        logger.info(
            "Deferred torrent for '%s' (guid=%s, source=%s, prowlarr=%s): %s",
            watchlist.title,
            watchlist.guid,
            entry.source.value,
            torrent_result.guid,
            saved.defer_reason,
        )
        return saved
