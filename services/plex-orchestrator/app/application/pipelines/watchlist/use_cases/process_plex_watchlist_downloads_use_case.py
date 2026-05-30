"""Thin coordinator: deferred queue, Deluge sync, then each Plex watchlist item."""
import logging

from app.application.deferred_downloads.use_cases.process_deferred_downloads_use_case import (
    ProcessDeferredDownloadsUseCase,
)
from app.application.pipelines.watchlist.models.watchlist_download_run_result import (
    ProcessPlexWatchlistDownloadsResult,
    WatchlistItemProcessOutcome,
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

    async def execute(self) -> ProcessPlexWatchlistDownloadsResult:
        result = ProcessPlexWatchlistDownloadsResult()

        release_result = await self._process_deferred_downloads_use_case.execute()
        result.deferred_released = release_result.sent
        result.deferred_still_pending = release_result.still_pending
        if release_result.sent:
            logger.info(
                "Released %s deferred torrent(s) to Deluge (still pending: %s)",
                release_result.sent,
                release_result.still_pending,
            )

        watchlist_entries = await self._get_watchlists_for_active_users.execute()
        result.watchlist_entries = len(watchlist_entries)

        sync_result = await self._reconcile_active_downloads_use_case.execute()
        if sync_result.get("skipped"):
            result.deluge_reconcile_skipped = True
            result.deluge_reconcile_reason = sync_result.get("reason")
            logger.warning(
                "Skipped torrent download DB sync with Deluge: reason=%s",
                sync_result.get("reason"),
            )
        else:
            result.deluge_removed = sync_result["removed_count"]
            result.deluge_updated = sync_result.get("updated_count", 0)
            result.deluge_total_checked = sync_result["total_checked"]
            logger.info(
                "Synced torrent download DB with Deluge: %s removed, %s updated out of %s checked",
                sync_result["removed_count"],
                sync_result.get("updated_count", 0),
                sync_result["total_checked"],
            )

        for entry in watchlist_entries:
            title = entry.item.title
            try:
                should_skip, skip_reason = (
                    await self._should_skip_watchlist_item_query.execute(entry)
                )
                if should_skip:
                    if skip_reason == "already_in_library":
                        result.skipped_already_in_library += 1
                    else:
                        result.skipped_already_queued += 1
                    continue

                outcome = await self._process_watchlist_item_use_case.execute(entry)
            except Exception:
                logger.exception(
                    "Watchlist item '%s' failed; continuing with remaining items",
                    title,
                )
                result.send_failed += 1
                continue

            if outcome == WatchlistItemProcessOutcome.SENT_TO_DELUGE:
                result.sent_to_deluge += 1
            elif outcome == WatchlistItemProcessOutcome.DEFERRED:
                result.deferred += 1
            elif outcome == WatchlistItemProcessOutcome.NO_TORRENT:
                result.no_torrent += 1
            else:
                result.send_failed += 1

        return result
