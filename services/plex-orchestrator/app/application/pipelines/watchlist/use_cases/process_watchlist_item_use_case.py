"""Search Prowlarr and download the best torrent for one watchlist item."""
import logging

from app.application.pipelines.watchlist.queries.get_missing_tv_episodes_query import (
    GetMissingTvEpisodesQuery,
)
from app.application.pipelines.watchlist.services.watchlist_search_builder import (
    WatchlistSearchQueryBuilder,
    is_show_watchlist,
)
from app.application.pipelines.watchlist.use_cases.try_send_torrent_for_watchlist_item_use_case import (
    TrySendTorrentForWatchlistItemUseCase,
)
from app.application.pipelines.watchlist.use_cases.remove_watchlist_entry_use_case import (
    RemoveWatchlistEntryUseCase,
)
from app.application.prowlarr.queries.find_best_torrent_query import GetBestTorrentsQuery
from app.application.active_downloads.use_cases.create_active_download_use_case import (
    CreateActiveDownloadUseCase,
)
from app.application.pipelines.watchlist.models.watchlist_download_run_result import (
    WatchlistItemProcessOutcome,
)
from app.domain.models.active_download import ActiveDownload
from app.domain.services.watchlist_download_tracking import (
    active_download_from_watchlist_entry,
)
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
        remove_watchlist_entry_use_case: RemoveWatchlistEntryUseCase,
        get_missing_tv_episodes_query: GetMissingTvEpisodesQuery,
    ):
        self._watchlist_search_query_builder = watchlist_search_query_builder
        self._find_best_torrent_query = find_best_torrent_query
        self._try_send_torrent_use_case = try_send_torrent_use_case
        self._create_active_download_use_case = create_active_download_use_case
        self._remove_watchlist_entry_use_case = remove_watchlist_entry_use_case
        self._get_missing_tv_episodes_query = get_missing_tv_episodes_query

    async def execute(self, entry: WatchlistItemForUser) -> WatchlistItemProcessOutcome:
        watchlist = entry.item
        if is_show_watchlist(watchlist):
            return await self._execute_show(entry)
        return await self._execute_movie(entry)

    async def _execute_movie(self, entry: WatchlistItemForUser) -> WatchlistItemProcessOutcome:
        watchlist = entry.item
        search_query = await self._watchlist_search_query_builder.execute(watchlist)
        torrent_search_results = await self._find_best_torrent_query.execute(
            search_query
        )
        if not torrent_search_results:
            logger.error("No torrent available for %s", search_query)
            return WatchlistItemProcessOutcome.NO_TORRENT

        return await self._try_torrent_results(
            entry,
            search_query=search_query,
            torrent_search_results=torrent_search_results,
            remove_watchlist_on_success=False,
        )

    async def _execute_show(self, entry: WatchlistItemForUser) -> WatchlistItemProcessOutcome:
        watchlist = entry.item
        all_missing = await self._get_missing_tv_episodes_query.execute(
            watchlist,
            entry.user_token() or "",
            plex_user_token=entry.plex_user_token,
            for_download=False,
        )
        if not all_missing:
            logger.info(
                "All catalog episodes present or queued for '%s'; removing watchlist",
                watchlist.title,
            )
            await self._remove_watchlist_entry_use_case.execute(entry)
            return WatchlistItemProcessOutcome.SENT_TO_DELUGE

        missing = await self._get_missing_tv_episodes_query.execute(
            watchlist,
            entry.user_token() or "",
            plex_user_token=entry.plex_user_token,
            for_download=True,
        )
        if not missing:
            logger.info(
                "No episodes in ahead buffer to download for '%s' right now",
                watchlist.title,
            )
            return WatchlistItemProcessOutcome.NO_TORRENT

        last_outcome = WatchlistItemProcessOutcome.NO_TORRENT
        for episode in missing:
            search_queries = (
                self._watchlist_search_query_builder.build_tv_episode_search_queries(
                    watchlist, episode
                )
            )
            torrent_search_results = []
            search_query = ""
            for query in search_queries:
                torrent_search_results = await self._find_best_torrent_query.execute(
                    query,
                    media_type="tv",
                    show_year=watchlist.year,
                )
                if torrent_search_results:
                    search_query = query
                    logger.info(
                        "Found torrents for '%s' using query '%s'",
                        watchlist.title,
                        query,
                    )
                    break
            if not torrent_search_results:
                logger.warning(
                    "No torrent for %s (tried: %s)",
                    watchlist.title,
                    search_queries,
                )
                continue

            outcome = await self._try_torrent_results(
                entry,
                search_query=search_query,
                torrent_search_results=torrent_search_results,
                remove_watchlist_on_success=False,
                season=episode.season,
                episode=episode.episode,
                episode_name=episode.name,
            )
            if outcome in (
                WatchlistItemProcessOutcome.SENT_TO_DELUGE,
                WatchlistItemProcessOutcome.DEFERRED,
            ):
                return outcome
            last_outcome = outcome

        return last_outcome

    async def _try_torrent_results(
        self,
        entry: WatchlistItemForUser,
        *,
        search_query: str,
        torrent_search_results,
        remove_watchlist_on_success: bool,
        season: int | None = None,
        episode: int | None = None,
        episode_name: str | None = None,
    ) -> WatchlistItemProcessOutcome:
        watchlist = entry.item
        user_token = entry.user_token()

        for index, torrent_result in enumerate(torrent_search_results):
            success, new_torrent, deferred = (
                await self._try_send_torrent_use_case.execute(
                    torrent_result,
                    entry,
                    search_query,
                    season=season,
                    episode=episode,
                    episode_name=episode_name,
                )
            )
            if deferred:
                logger.info(
                    "Deferred '%s' — watchlist item kept until download volume has space",
                    watchlist.title,
                )
                return WatchlistItemProcessOutcome.DEFERRED
            if success and new_torrent is not None:
                await self._create_active_download_use_case.execute(
                    active_download_from_watchlist_entry(
                        entry,
                        prowlarr_guid=torrent_result.guid,
                        uid=new_torrent.hash,
                        file_name=new_torrent.file_name,
                        season=season,
                        episode=episode,
                        episode_name=episode_name,
                    )
                )
                return WatchlistItemProcessOutcome.SENT_TO_DELUGE

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
        return WatchlistItemProcessOutcome.SEND_FAILED
