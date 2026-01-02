from typing import Protocol, List, Optional
from app.domain.models.media import MediaItem

class PlexWatchlistProvider(Protocol):
    async def get_watchlist(self, user_token: str) -> List[MediaItem]:
        """Get watchlist from Plex."""
        ...
    async def add_item(self, ratingKey: str, user_token: str) -> None:
        """Add item to Plex watchlist."""
        ...
    async def delete_item(self, ratingKey: str, user_token: str) -> None:
        """Delete item from Plex."""
        ...