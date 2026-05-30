"""Persist a torrent for later Prowlarr/Deluge send when download volume has space."""
import logging

from app.domain.models.deferred_download import DeferredDownload
from app.domain.models.torrent_search import TorrentSearchResult
from app.domain.ports.repositories.deferred_downloads.deferred_download_repository_port import (
    DeferredDownloadRepositoryPort,
)
from app.domain.services.download_volume_space_checker import DownloadVolumeSpaceChecker
from app.domain.services.media_identity import normalize_media_type_for_queue_match

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
        watchlist,
        user_token: str,
        torrent_result: TorrentSearchResult,
        search_query: str,
    ) -> DeferredDownload:
        reason = self._space_checker.defer_reason_for_torrent(torrent_result.size)
        item = DeferredDownload(
            guid_plex=watchlist.guid,
            rating_key=watchlist.rating_key,
            plex_user_token=user_token,
            guid_prowlarr=torrent_result.guid or "",
            indexer_id=torrent_result.indexerId or 0,
            torrent_title=torrent_result.title,
            media_title=watchlist.title,
            year=watchlist.year,
            media_type=normalize_media_type_for_queue_match(
                str(watchlist.type.value if hasattr(watchlist.type, "value") else watchlist.type)
            )
            or "movie",
            search_query=search_query,
            size_bytes=torrent_result.size,
            magnet_url=torrent_result.magnetUrl,
            defer_reason=reason or "deferred",
        )
        saved = await self._deferred_repo.upsert_pending(item)
        logger.info(
            "Deferred torrent for '%s' (plex=%s, prowlarr=%s): %s",
            watchlist.title,
            watchlist.guid,
            torrent_result.guid,
            saved.defer_reason,
        )
        return saved
