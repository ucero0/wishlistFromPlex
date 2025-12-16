"""query for checking if a media item is in a Plex library."""
from app.domain.models.media import MediaItem
from app.adapters.external.plexServer.adapter import PlexServerLibraryAdapter

class IsItemInLibraryQuery:
    def __init__(self, adapter: PlexServerLibraryAdapter):
        self.adapter = adapter
    
    async def execute(self, user_token: str, media: MediaItem) -> bool:
        return await self.adapter.is_item_in_library(user_token, media)