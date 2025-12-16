from app.domain.models.media import MediaItem
from app.adapters.external.plexClient.adapter import PlexWatchlistAdapter
from typing import List

class GetWatchListQuery:
    def __init__(self, adapter: PlexWatchlistAdapter):
        self.adapter = adapter

    async def execute(self, user_token: str) -> List[MediaItem]:
        return await self.adapter.get_watchlist(user_token)
