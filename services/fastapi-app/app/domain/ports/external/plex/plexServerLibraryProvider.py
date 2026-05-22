"""Port for Plex server library provider."""
from typing import Protocol

from app.domain.models.external_connection import ExternalConnectionStatus
from app.domain.models.media import MediaItem
from app.domain.models.plexLibraryLocations import PlexLibraryLocationsByMedia


class PlexServerLibraryProvider(Protocol):
    """Protocol for Plex server library operations."""

    async def test_connection(self) -> ExternalConnectionStatus:
        """Probe Plex server reachability (non-throwing)."""
        ...

    async def is_item_in_library(self, user_token: str, media: MediaItem) -> bool:
        ...

    async def get_library_locations_by_media(
        self, user_token: str
    ) -> PlexLibraryLocationsByMedia:
        ...

    async def partial_scan_library(
        self,
        user_token: str,
        section_id: int,
        folder_path: str,
    ) -> bool:
        ...
