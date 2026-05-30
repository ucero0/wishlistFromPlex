from typing import List
from app.domain.models.media import MediaItem
from app.domain.ports.external.plex.plex_watchlist_provider import PlexWatchlistProvider
from app.infrastructure.external_apis.plex.plex_client.client import PlexWatchlistClient
from app.infrastructure.external_apis.plex.plex_client.schemas import PlexWatchlistItemDTO
from app.adapters.external.plex_client.mapper import to_domain

class PlexWatchlistAdapter(PlexWatchlistProvider):
    """Adapter for Plex watchlist."""
    def __init__(self, client: PlexWatchlistClient):
        self.client = client

    async def get_watchlist(self, user_token: str) -> List[MediaItem]:
        raw = await self.client.get_watchlist_raw(user_token)
        items = raw.get("MediaContainer", {}).get("Metadata", [])
        dtos = [PlexWatchlistItemDTO(**item) for item in items]
        return [to_domain(dto) for dto in dtos]

    async def add_item(self, rating_key: str, user_token: str) -> None:
        await self.client.add_item_raw(rating_key, user_token)

    async def delete_item(self, rating_key: str, user_token: str) -> None:
        await self.client.delete_item_raw(rating_key, user_token)
        
