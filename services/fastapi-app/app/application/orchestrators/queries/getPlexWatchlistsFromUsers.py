"""Merge Plex watchlists from all active users, one entry per media (by Plex guid)."""
from app.application.plex.queries.getPlexUsers import GetPlexUserQuery
from app.application.plex.queries.getWatchList import GetWatchListQuery
from app.domain.models.media import MediaItem
from app.domain.models.plexUser import PlexUser
from typing import List


class GetPlexWatchlistsFromUsers:
    def __init__(
        self,
        getPlexUserQuery: GetPlexUserQuery,
        getWatchListQuery: GetWatchListQuery,
    ):
        self.getPlexUserQuery = getPlexUserQuery
        self.getWatchListQuery = getWatchListQuery

    async def execute(self) -> tuple[str, List[MediaItem]]:
        plex_users: List[PlexUser] = await self.getPlexUserQuery.execute()
        if not plex_users:
            return "", []

        merged: List[MediaItem] = []
        seen_guids: set[str] = set()

        for user in plex_users:
            watchlist = await self.getWatchListQuery.execute(user.plex_token)
            for item in watchlist:
                if item.guid in seen_guids:
                    continue
                seen_guids.add(item.guid)
                merged.append(item)

        return plex_users[0].plex_token, merged
