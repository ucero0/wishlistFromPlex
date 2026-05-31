"""query for checking if a media item is in a Plex library."""
from app.domain.models.media import MediaItem
from app.domain.ports.external.plex.plex_server_library_provider import PlexServerLibraryProvider
from app.domain.services.tmdb_guid import parse_tmdb_guid


class IsItemInLibraryQuery:
    def __init__(self, provider: PlexServerLibraryProvider):
        self.provider = provider

    async def execute(self, media: MediaItem) -> bool:
        if media.plex_library_guid:
            return await self.provider.is_item_in_library(
                media.model_copy(update={"guid": media.plex_library_guid})
            )
        parsed = parse_tmdb_guid(media.guid or "")
        if parsed:
            media_type, tmdb_id = parsed
            return await self.provider.is_tmdb_item_in_library(
                tmdb_id, media_type, media
            )
        return await self.provider.is_item_in_library(media)
