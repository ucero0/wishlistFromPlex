"""Adapter for Plex server library API."""
import logging

from app.adapters.external.plexServer import mapper as plex_server_mapper
from app.domain.models.media import MediaItem
from app.domain.models.plexLibraryLocations import PlexLibraryLocationsByMedia
from app.domain.ports.external.plex.plexServerLibraryProvider import PlexServerLibraryProvider
from app.infrastructure.externalApis.plex.plexServer.client import PlexServerLibraryApiClient

logger = logging.getLogger(__name__)

class PlexServerLibraryAdapter(PlexServerLibraryProvider):
    """Adapter that converts between Plex infrastructure and domain models."""
    def __init__(self, client: PlexServerLibraryApiClient):
        self.client = client
    
    async def is_item_in_library(self, user_token: str, media: MediaItem) -> bool:
        """Check if an item is in the Plex library."""
        logger.info(f"Checking if item is in library: guid={media.guid}, type={media.type}")
        mediaInt = None
        if media.type == "movie":
            mediaInt = 1
        elif media.type == "show":
            mediaInt = 2
        else:
            logger.warning(f"Unknown media type: {media.type}, will not filter by type")

        response = await self.client.get_library_items_raw(user_token, media.guid, mediaInt)
        # Extract size from JSON response: MediaContainer.size
        media_container = response.MediaContainer
        size = int(media_container.get("size", 0))
        if size == 1:
            metadata = media_container.get("Metadata", [])
            logger.debug(f"metadata: {metadata}")
            data = metadata[0].get("guid")
            logger.debug(f"Data: {data}")
            if data == media.guid:
                result = True
            else:
                logger.warning(f"Metadata is not a list or is empty: {metadata}")
                result = False
        else:
            result = False
        logger.info(f"Library check result: size={size}, has_media={result}")
        return result

    async def get_library_locations_by_media(
        self, user_token: str
    ) -> PlexLibraryLocationsByMedia:
        """Load library sections and paths for movie/TV from Plex Server."""
        raw = await self.client.get_library_locations_by_media_raw(user_token)
        return plex_server_mapper.library_locations_response_to_domain(raw)

    async def partial_scan_library(
        self, 
        user_token: str, 
        section_id: int, 
        folder_path: str
    ) -> bool:
        """Trigger a partial scan of a specific folder in the Plex library."""
        return await self.client.partial_scan_library_raw(user_token, section_id, folder_path)