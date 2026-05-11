"""Port for Plex server library provider."""
from typing import Protocol

from app.domain.models.media import MediaItem
from app.domain.models.plexLibraryLocations import PlexLibraryLocationsByMedia


class PlexServerLibraryProvider(Protocol):
    """Protocol for checking if items are in Plex library."""
    async def is_item_in_library(self, user_token: str, media: MediaItem) -> bool:
        """Check if an item is in the Plex library."""
        ...

    async def get_library_locations_by_media(
        self, user_token: str
    ) -> PlexLibraryLocationsByMedia:
        """Return movie and TV library sections with their configured root paths."""
        ...

    async def partial_scan_library(
        self, 
        user_token: str, 
        section_id: int, 
        folder_path: str
    ) -> bool:
        """
        Trigger a partial scan of a specific folder in the Plex library.
        
        Args:
            user_token: Plex user token
            section_id: Library section ID
            folder_path: Absolute path to the folder to scan
            
        Returns:
            True if successful, False otherwise
        """
        ...