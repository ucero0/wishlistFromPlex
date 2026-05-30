"""Search Prowlarr and download the best torrent for one watchlist item."""
import logging

from app.application.pipelines.watchlist.services.watchlist_search_builder import (
    WatchlistSearchQueryBuilder,
)
from app.application.pipelines.watchlist.use_cases.try_send_torrent_for_watchlist_item_use_case import (
    TrySendTorrentForWatchlistItemUseCase,
)
from app.application.plex.use_cases.remove_watchlist_item_use_case import RemoveWatchlistItemUseCase
from app.application.prowlarr.queries.find_best_torrent_query import GetBestTorrentsQuery
from app.application.active_downloads.use_cases.create_active_download_use_case import (
    CreateActiveDownloadUseCase,
)
from app.domain.models.active_download import ActiveDownload
from app.domain.models.watchlist_item_for_user import WatchlistItemForUser

logger = logging.getLogger(__name__)


class ProcessWatchlistItemUseCase:
    """Find torrents for one watchlist row and track the first successful download."""

    def __init__(
        self,
        watchlist_search_query_builder: WatchlistSearchQueryBuilder,
        find_best_torrent_query: GetBestTorrentsQuery,
        try_send_torrent_use_case: TrySendTorrentForWatchlistItemUseCase,
        create_active_download_use_case: CreateActiveDownloadUseCase,
        remove_watchlist_item_use_case: RemoveWatchlistItemUseCase,
    ):
        self._watchlist_search_query_builder = watchlist_search_query_builder
        self._find_best_torrent_query = find_best_torrent_query
        self._try_send_torrent_use_case = try_send_torrent_use_case
        self._create_active_download_use_case = create_active_download_use_case
        self._remove_watchlist_item_use_case = remove_watchlist_item_use_case

    async def execute(self, entry: WatchlistItemForUser) -> bool:
        watchlist = entry.item
        user_token = entry.plex_user_token
        search_query = await self._watchlist_search_query_builder.execute(watchlist)
        torrent_search_results = await self._find_best_torrent_query.execute(
            search_query
        )
        if not torrent_search_results:
            logger.error("No torrent available for %s", search_query)
            return False

        for index, torrent_result in enumerate(torrent_search_results):
            success, new_torrent, deferred = (
                await self._try_send_torrent_use_case.execute(
                    torrent_result, watchlist, user_token, search_query
                )
            )
            if deferred:
                logger.info(
                    "Deferred '%s' — watchlist item kept until download volume has space",
                    watchlist.title,
                )
                return True
            if success and new_torrent is not None:
                await self._create_active_download_use_case.execute(
                    ActiveDownload(
                        plex_guid=watchlist.guid,
                        watchlist_item_id=watchlist.rating_key,
                        plex_user_token=user_token,
                        prowlarr_guid=torrent_result.guid,
                        uid=new_torrent.hash,
                        title=watchlist.title,
                        file_name=new_torrent.file_name,
                        year=watchlist.year,
                        type=watchlist.type,
                    )
                )
                await self._remove_watchlist_item_use_case.execute(
                    watchlist.rating_key, user_token
                )
                return True

            logger.info(
                "Trying next torrent result for '%s' (attempt %s/%s)",
                watchlist.title,
                index + 1,
                len(torrent_search_results),
            )

        logger.error(
            "Failed to download any torrent for '%s' after trying %s result(s)",
            watchlist.title,
            len(torrent_search_results),
        )
        return False
