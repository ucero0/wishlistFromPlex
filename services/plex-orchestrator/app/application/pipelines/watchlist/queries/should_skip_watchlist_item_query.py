"""Decide whether a watchlist row can be skipped before torrent search."""

import logging

from typing import Optional, Tuple



from app.application.pipelines.watchlist.queries.is_media_already_queued_query import (

    IsMediaAlreadyQueuedQuery,

)

from app.application.pipelines.watchlist.services.watchlist_search_builder import (

    watchlist_media_type,

)

from app.application.plex.queries.get_plex_server_item_query import IsItemInLibraryQuery

from app.application.plex.use_cases.remove_watchlist_item_use_case import RemoveWatchlistItemUseCase

from app.domain.models.watchlist_item_for_user import WatchlistItemForUser



logger = logging.getLogger(__name__)





class ShouldSkipWatchlistItemQuery:

    """Skip items already in the library or already queued for download."""



    def __init__(

        self,

        is_item_in_library_query: IsItemInLibraryQuery,

        is_media_already_queued_query: IsMediaAlreadyQueuedQuery,

        remove_watchlist_item_use_case: RemoveWatchlistItemUseCase,

    ):

        self._is_item_in_library_query = is_item_in_library_query

        self._is_media_already_queued_query = is_media_already_queued_query

        self._remove_watchlist_item_use_case = remove_watchlist_item_use_case



    async def execute(

        self, entry: WatchlistItemForUser

    ) -> Tuple[bool, Optional[str]]:

        watchlist = entry.item

        if await self._is_item_in_library_query.execute(watchlist):

            logger.info(

                "Removing %s from watchlist because it is already in the library",

                watchlist.title,

            )

            await self._remove_watchlist_item_use_case.execute(

                watchlist.rating_key, entry.plex_user_token

            )

            return True, "already_in_library"



        queued, queue_reason = await self._is_media_already_queued_query.execute(

            watchlist.guid,

            title=watchlist.title,

            year=watchlist.year,

            media_type=watchlist_media_type(watchlist),

        )

        if queued:

            logger.info(

                "Skipping '%s' — already handled for another user (%s)",

                watchlist.title,

                queue_reason,

            )

            if watchlist.rating_key:

                await self._remove_watchlist_item_use_case.execute(

                    watchlist.rating_key, entry.plex_user_token

                )

            return True, queue_reason or "already_queued"



        return False, None

