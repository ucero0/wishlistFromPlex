"""Merge Plex and TMDB watchlists from all active users."""
from typing import List

from app.application.plex.queries.get_plex_users_query import GetPlexUserQuery
from app.application.plex.queries.get_watchlist_query import GetWatchlistQuery
from app.application.tmdb.queries.get_tmdb_users_query import GetTmdbUserQuery
from app.application.tmdb.queries.get_tmdb_watchlist_query import GetTmdbWatchlistQuery
from app.domain.models.watchlist_item_for_user import WatchlistItemForUser
from app.domain.models.watchlist_source import WatchlistSource


class GetWatchlistsForActiveUsersQuery:
    def __init__(
        self,
        get_plex_user_query: GetPlexUserQuery,
        get_watchlist_query: GetWatchlistQuery,
        get_tmdb_user_query: GetTmdbUserQuery,
        get_tmdb_watchlist_query: GetTmdbWatchlistQuery,
    ):
        self._get_plex_user_query = get_plex_user_query
        self._get_watchlist_query = get_watchlist_query
        self._get_tmdb_user_query = get_tmdb_user_query
        self._get_tmdb_watchlist_query = get_tmdb_watchlist_query

    async def execute(self) -> List[WatchlistItemForUser]:
        merged: List[WatchlistItemForUser] = []
        seen_guids: set[str] = set()

        plex_users = await self._get_plex_user_query.execute()
        plex_user_token = plex_users[0].plex_token if plex_users else None

        for user in plex_users:
            if user.id is None:
                continue
            watchlist = await self._get_watchlist_query.execute(user.plex_token)
            for item in watchlist:
                if item.guid in seen_guids:
                    continue
                seen_guids.add(item.guid)
                merged.append(
                    WatchlistItemForUser(
                        item=item,
                        source=WatchlistSource.PLEX,
                        plex_user_id=user.id,
                        plex_user_token=user.plex_token,
                    )
                )

        for user in await self._get_tmdb_user_query.execute():
            if user.id is None or user.account_id is None:
                continue
            watchlist = await self._get_tmdb_watchlist_query.execute(
                user.account_id, user.access_token
            )
            for item in watchlist:
                if item.guid in seen_guids:
                    continue
                seen_guids.add(item.guid)
                merged.append(
                    WatchlistItemForUser(
                        item=item,
                        source=WatchlistSource.TMDB,
                        tmdb_user_id=user.id,
                        tmdb_account_id=user.account_id,
                        tmdb_access_token=user.access_token,
                        plex_user_token=plex_user_token,
                    )
                )

        return merged
