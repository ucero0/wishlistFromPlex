from app.application.plex.queries.getPlexUsers import GetPlexUserQuery
from app.application.plex.queries.getWatchList import GetWatchListQuery
from app.domain.models.media import MediaItem
from app.domain.models.plexUser import PlexUser
from typing import List
class GetPlexWatchlistsFromUsers:
    def __init__(self, 
    getPlexUserQuery: GetPlexUserQuery,
    getWatchListQuery: GetWatchListQuery
    ):
        self.getPlexUserQuery = getPlexUserQuery
        self.getWatchListQuery = getWatchListQuery

    async def execute(self) -> List[MediaItem]:
        plex_users: List[PlexUser] = await self.getPlexUserQuery.execute()
        watchlists: List[MediaItem] = []
        for index, user in enumerate(plex_users):
            watchlist = await self.getWatchListQuery.execute(user.plex_token)
            if index == 0:
                watchlists = watchlist
            else:
                for item in watchlist:
                    if not item.guid in watchlists:
                        watchlists.append(item)
        return watchlists