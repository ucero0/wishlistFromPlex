"""Thin coordinator: deferred queue, Deluge sync, then each Plex watchlist item."""
import logging

from app.application.deferred_downloads.use_cases.process_deferred_downloads_use_case import (
    ProcessDeferredDownloadsUseCase,
)
from app.application.pipelines.watchlist.queries.get_watchlists_for_active_users_query import (
    GetWatchlistsForActiveUsersQuery,
)
from app.application.pipelines.watchlist.queries.should_skip_watchlist_item_query import (
    ShouldSkipWatchlistItemQuery,
)
from app.application.pipelines.watchlist.use_cases.process_watchlist_item_use_case import (
    ProcessWatchlistItemUseCase,
)
from app.application.pipelines.watchlist.use_cases.reconcile_active_downloads_with_deluge_use_case import (
    ReconcileActiveDownloadsWithDelugeUseCase,
)
from app.application.plex.queries.get_plex_users_query import GetPlexUserQuery
from app.application.plex.queries.get_watchlist_query import GetWatchlistQuery

logger = logging.getLogger(__name__)


class ProcessPlexWatchlistDownloadsUseCase:
    def __init__(
        self,
        get_plex_user_query: GetPlexUserQuery,
        get_watchlist_query: GetWatchlistQuery,
        reconcile_active_downloads_use_case: ReconcileActiveDownloadsWithDelugeUseCase,
        process_deferred_downloads_use_case: ProcessDeferredDownloadsUseCase,
        should_skip_watchlist_item_query: ShouldSkipWatchlistItemQuery,
        process_watchlist_item_use_case: ProcessWatchlistItemUseCase,
    ):
        self._get_watchlists_for_active_users = GetWatchlistsForActiveUsersQuery(
            get_plex_user_query, get_watchlist_query
        )
        self._reconcile_active_downloads_use_case = reconcile_active_downloads_use_case
        self._process_deferred_downloads_use_case = (
            process_deferred_downloads_use_case
        )
        self._should_skip_watchlist_item_query = should_skip_watchlist_item_query
        self._process_watchlist_item_use_case = process_watchlist_item_use_case

    async def execute(self) -> None:
        release_result = await self._process_deferred_downloads_use_case.execute()
        if release_result.sent:
            logger.info(
                "Released %s deferred torrent(s) to Deluge (still pending: %s)",
                release_result.sent,
                release_result.still_pending,
            )

        watchlist_entries = await self._get_watchlists_for_active_users.execute()

        sync_result = await self._reconcile_active_downloads_use_case.execute()
        if sync_result.get("skipped"):
            logger.warning(
                "Skipped torrent download DB sync with Deluge: reason=%s",
                sync_result.get("reason"),
            )
        else:
            logger.info(
                "Synced torrent download DB with Deluge: %s removed, %s updated out of %s checked",
                sync_result["removed_count"],
                sync_result.get("updated_count", 0),
                sync_result["total_checked"],
            )

        for entry in watchlist_entries:
            should_skip, _ = await self._should_skip_watchlist_item_query.execute(
                entry
            )
            if should_skip:
                continue
            await self._process_watchlist_item_use_case.execute(entry)
