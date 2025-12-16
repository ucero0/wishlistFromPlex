"""Port for Plex server library provider."""
from typing import Protocol
from app.domain.models.media import MediaItem


class PlexServerLibraryProvider(Protocol):
    """Protocol for checking if items are in Plex library."""
    async def is_item_in_library(self, user_token: str, media: MediaItem) -> bool:
        """Check if an item is in the Plex library."""
        ...
