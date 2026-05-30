from app.domain.models.media import MediaItem
from app.domain.ports.external.plex.plex_watchlist_provider import PlexWatchlistProvider
from typing import List

class GetWatchlistQuery:
    def __init__(self, provider: PlexWatchlistProvider):
        self.provider = provider

    async def execute(self, user_token: str) -> List[MediaItem]:
        return await self.provider.get_watchlist(user_token)
