from typing import List
from app.domain.models.media import MediaItem
from app.domain.ports.external.plex.plexWatchListProvider import PlexWatchlistProvider
from app.infrastructure.externalApis.plex.plexClient.client import PlexWatchlistClient
from app.infrastructure.externalApis.plex.plexClient.schemas import PlexWatchlistItemDTO
from app.adapters.external.plexClient.mapper import to_domain

class PlexWatchlistAdapter(PlexWatchlistProvider):
    """Adapter for Plex watchlist."""
    def __init__(self, client: PlexWatchlistClient):
        self.client = client

    async def get_watchlist(self, user_token: str) -> List[MediaItem]:
        raw = await self.client.get_watchlist_raw(user_token)
        items = raw.get("MediaContainer", {}).get("Metadata", [])
        dtos = [PlexWatchlistItemDTO(**item) for item in items]
        return [to_domain(dto) for dto in dtos]

    async def delete_item(self, media: MediaItem, user_token: str) -> None:
        await self.client.delete_item_raw(media.ratingKey, user_token)
        
