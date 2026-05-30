"""Merge Plex watchlists from all active users, one entry per media (by Plex guid)."""

from typing import List



from app.application.plex.queries.get_plex_users_query import GetPlexUserQuery

from app.application.plex.queries.get_watchlist_query import GetWatchlistQuery

from app.domain.models.watchlist_item_for_user import WatchlistItemForUser

from app.domain.models.plex_user import PlexUser





class GetWatchlistsForActiveUsersQuery:

    def __init__(

        self,

        get_plex_user_query: GetPlexUserQuery,

        get_watchlist_query: GetWatchlistQuery,

    ):

        self._get_plex_user_query = get_plex_user_query

        self._get_watchlist_query = get_watchlist_query



    async def execute(self) -> List[WatchlistItemForUser]:

        plex_users: List[PlexUser] = await self._get_plex_user_query.execute()

        if not plex_users:

            return []



        merged: List[WatchlistItemForUser] = []

        seen_guids: set[str] = set()



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

                        plex_user_id=user.id,

                        plex_user_token=user.plex_token,

                    )

                )



        return merged

