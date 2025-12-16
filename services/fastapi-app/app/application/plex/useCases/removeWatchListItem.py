from app.domain.models.media import MediaItem
from app.adapters.external.plexClient.adapter import PlexWatchlistAdapter

class RemoveWatchListItemUseCase:
    def __init__(self, adapter: PlexWatchlistAdapter):
        self.adapter = adapter

    async def execute(self, media: MediaItem, user_token: str) -> None:
        return await self.adapter.delete_item(media, user_token)
        