"""Adapter for Plex server library API."""
from app.domain.ports.external.plex.plexServerLibraryProvider import PlexServerLibraryProvider
from app.domain.models.media import MediaItem
from app.infrastructure.externalApis.plex.plexServer.client import PlexServerLibraryApiClient
import logging

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

        logger.debug(f"Converted media type to integer: {mediaInt}")
        response_json = await self.client.get_library_items_raw(user_token, media.guid, mediaInt)
        # Extract size from JSON response: MediaContainer.size
        media_container = response_json.get("MediaContainer", {})
        size = int(media_container.get("size", 0))
        result = size > 0
        logger.info(f"Library check result: size={size}, has_media={result}")
        return result