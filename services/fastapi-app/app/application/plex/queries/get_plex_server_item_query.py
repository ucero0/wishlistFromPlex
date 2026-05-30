"""query for checking if a media item is in a Plex library."""
from app.domain.models.media import MediaItem
from app.domain.ports.external.plex.plex_server_library_provider import PlexServerLibraryProvider

class IsItemInLibraryQuery:
    def __init__(self, provider: PlexServerLibraryProvider):
        self.provider = provider
    
    async def execute(self, media: MediaItem) -> bool:
        return await self.provider.is_item_in_library(media)