"""Adapter for Plex server library API."""
import logging

from app.adapters.external.plex_server import mapper as plex_server_mapper
from app.domain.models.external_connection import ExternalConnectionStatus
from app.domain.models.media import MediaItem
from app.domain.models.plex_library_locations import PlexLibraryLocationsByMedia
from app.domain.ports.external.plex.plex_server_library_provider import (
    PlexServerLibraryProvider,
)
from app.domain.services.connection_probe import capture_async_connection_probe
from app.infrastructure.external_apis.plex.plex_server.client import (
    PlexServerLibraryApiClient,
)

logger = logging.getLogger(__name__)


class PlexServerLibraryAdapter(PlexServerLibraryProvider):
    """Adapter that converts between Plex infrastructure and domain models."""

    def __init__(self, client: PlexServerLibraryApiClient):
        self.client = client

    async def test_connection(self) -> ExternalConnectionStatus:
        return await capture_async_connection_probe(
            "plex",
            self.client.probe_connection,
        )

    async def is_item_in_library(self, media: MediaItem) -> bool:
        logger.info(
            "Checking if item is in library: guid=%s, type=%s", media.guid, media.type
        )
        media_int = None
        if media.type == "movie":
            media_int = 1
        elif media.type == "show":
            media_int = 2
        else:
            logger.warning("Unknown media type: %s, will not filter by type", media.type)

        response = await self.client.get_library_items_raw(media.guid, media_int)
        media_container = response.MediaContainer
        size = int(media_container.get("size", 0))
        if size == 1:
            metadata = media_container.get("Metadata", [])
            if metadata and metadata[0].get("guid") == media.guid:
                return True
            return False
        return False

    async def get_library_locations_by_media(
        self,
    ) -> PlexLibraryLocationsByMedia:
        raw = await self.client.get_library_locations_by_media_raw()
        return plex_server_mapper.library_locations_response_to_domain(raw)

    async def partial_scan_library(
        self,
        section_id: int,
        folder_path: str,
    ) -> bool:
        return await self.client.partial_scan_library_raw(section_id, folder_path)
