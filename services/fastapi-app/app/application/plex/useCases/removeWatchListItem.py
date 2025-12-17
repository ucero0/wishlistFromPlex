from app.domain.models.media import MediaItem
from app.adapters.external.plexClient.adapter import PlexWatchlistAdapter

class RemoveWatchListItemUseCase:
    def __init__(self, adapter: PlexWatchlistAdapter):
        self.adapter = adapter

    async def execute(self, ratingKey: str, user_token: str) -> None:
        return await self.adapter.delete_item(ratingKey, user_token)
        