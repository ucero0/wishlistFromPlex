"""Decide whether a watchlist row can be skipped before torrent search."""

import logging

from typing import Optional, Tuple

from app.application.pipelines.watchlist.queries.get_missing_tv_episodes_query import (
    GetMissingTvEpisodesQuery,
)
from app.application.pipelines.watchlist.queries.is_media_already_queued_query import (
    IsMediaAlreadyQueuedQuery,
)
from app.application.pipelines.watchlist.services.watchlist_search_builder import (
    is_show_watchlist,
    watchlist_media_type,
)
from app.application.plex.queries.get_plex_server_item_query import IsItemInLibraryQuery
from app.application.pipelines.watchlist.use_cases.remove_watchlist_entry_use_case import (
    RemoveWatchlistEntryUseCase,
)
from app.domain.models.watchlist_item_for_user import WatchlistItemForUser

logger = logging.getLogger(__name__)


class ShouldSkipWatchlistItemQuery:
    """Skip items already in the library or already queued for download."""

    def __init__(
        self,
        is_item_in_library_query: IsItemInLibraryQuery,
        is_media_already_queued_query: IsMediaAlreadyQueuedQuery,
        remove_watchlist_entry_use_case: RemoveWatchlistEntryUseCase,
        get_missing_tv_episodes_query: GetMissingTvEpisodesQuery,
    ):
        self._is_item_in_library_query = is_item_in_library_query
        self._is_media_already_queued_query = is_media_already_queued_query
        self._remove_watchlist_entry_use_case = remove_watchlist_entry_use_case
        self._get_missing_tv_episodes_query = get_missing_tv_episodes_query

    async def execute(
        self, entry: WatchlistItemForUser
    ) -> Tuple[bool, Optional[str]]:
        watchlist = entry.item

        if is_show_watchlist(watchlist):
            return await self._execute_show(entry)

        if await self._is_item_in_library_query.execute(watchlist):
            logger.info(
                "Removing %s from watchlist because it is already in the library",
                watchlist.title,
            )
            await self._remove_watchlist_entry_use_case.execute(entry)
            return True, "already_in_library"

        queued, queue_reason = await self._is_media_already_queued_query.execute_for_watchlist(
            watchlist
        )
        if queued:
            logger.info(
                "Skipping '%s' — already handled (%s)",
                watchlist.title,
                queue_reason,
            )
            if self._remove_watchlist_entry_use_case.should_remove_when_already_queued(
                queue_reason
            ):
                await self._remove_watchlist_entry_use_case.execute(entry)
            return True, queue_reason or "already_queued"

        return False, None

    async def _execute_show(
        self, entry: WatchlistItemForUser
    ) -> Tuple[bool, Optional[str]]:
        watchlist = entry.item
        missing = await self._get_missing_tv_episodes_query.execute(
            watchlist,
            entry.user_token() or "",
            plex_user_token=entry.plex_user_token,
        )
        if not missing:
            logger.info(
                "Removing '%s' from watchlist — all catalog episodes present or queued",
                watchlist.title,
            )
            await self._remove_watchlist_entry_use_case.execute(entry)
            return True, "show_complete"

        return False, None
