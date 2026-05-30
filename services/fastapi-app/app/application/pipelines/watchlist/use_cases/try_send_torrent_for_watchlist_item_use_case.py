"""Attempt to send one Prowlarr result to Deluge (or defer it)."""
import logging
from typing import Optional, Tuple

from app.application.blacklist_torrent.queries import IsBlacklistedByGuidProwlarrQuery
from app.application.deferred_downloads.use_cases.enqueue_deferred_download_use_case import (
    EnqueueDeferredDownloadUseCase,
)
from app.application.pipelines.watchlist.queries.is_media_already_queued_query import (
    IsMediaAlreadyQueuedQuery,
)
from app.application.pipelines.watchlist.services.watchlist_search_builder import (
    watchlist_media_type,
)
from app.application.plex.use_cases.remove_watchlist_item_use_case import RemoveWatchlistItemUseCase
from app.application.active_downloads.services.send_torrent_to_deluge_service import SendTorrentToDelugeService
from app.domain.models.torrent import Torrent
from app.domain.models.torrent_search import TorrentSearchResult
from app.domain.services.download_volume_space_checker import DownloadVolumeSpaceChecker

logger = logging.getLogger(__name__)


class TrySendTorrentForWatchlistItemUseCase:
    """
    Try one torrent release for a watchlist item.

    Returns (success, deluge_torrent, deferred).
    """

    def __init__(
        self,
        is_blacklisted_query: IsBlacklistedByGuidProwlarrQuery,
        is_media_already_queued_query: IsMediaAlreadyQueuedQuery,
        remove_watchlist_item_use_case: RemoveWatchlistItemUseCase,
        download_volume_space_checker: DownloadVolumeSpaceChecker,
        enqueue_deferred_use_case: EnqueueDeferredDownloadUseCase,
        send_torrent_to_deluge_service: SendTorrentToDelugeService,
    ):
        self._is_blacklisted_query = is_blacklisted_query
        self._is_media_already_queued_query = is_media_already_queued_query
        self._remove_watchlist_item_use_case = remove_watchlist_item_use_case
        self._download_volume_space_checker = download_volume_space_checker
        self._enqueue_deferred_use_case = enqueue_deferred_use_case
        self._send_torrent_to_deluge_service = send_torrent_to_deluge_service

    async def execute(
        self,
        torrent_result: TorrentSearchResult,
        watchlist,
        user_token: str,
        search_query: str,
    ) -> Tuple[bool, Optional[Torrent], bool]:
        if await self._is_blacklisted_query.execute(torrent_result.guid):
            logger.warning(
                "Torrent '%s' is blacklisted, skipping", torrent_result.title
            )
            return False, None, False

        if torrent_result.guid:
            queued, queue_reason = await self._is_media_already_queued_query.execute(
                watchlist.guid,
                guid_prowlarr=torrent_result.guid,
                title=watchlist.title,
                year=watchlist.year,
                media_type=watchlist_media_type(watchlist),
            )
            if queued:
                logger.info(
                    "Not sending '%s' to Deluge — same release already queued (%s)",
                    watchlist.title,
                    queue_reason,
                )
                if watchlist.rating_key:
                    await self._remove_watchlist_item_use_case.execute(
                        watchlist.rating_key, user_token
                    )
                return False, None, True

        ok, _, _ = self._download_volume_space_checker.has_space_for_torrent(
            torrent_result.size
        )
        if not ok:
            await self._enqueue_deferred_use_case.execute(
                watchlist=watchlist,
                user_token=user_token,
                torrent_result=torrent_result,
                search_query=search_query,
            )
            return False, None, True

        new_torrent = await self._send_torrent_to_deluge_service.execute(torrent_result)
        if new_torrent is None:
            logger.warning(
                "Torrent '%s' is not added to deluge, download failed",
                torrent_result.title,
            )
            return False, None, False

        logger.info(
            "Torrent '%s' is added to deluge successfully, download successful",
            torrent_result.title,
        )
        return True, new_torrent, False
