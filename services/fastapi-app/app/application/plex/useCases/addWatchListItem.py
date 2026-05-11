from app.domain.ports.external.plex.plexWatchListProvider import PlexWatchlistProvider

class AddWatchListItemUseCase:
    def __init__(self, provider: PlexWatchlistProvider):
        self.provider = provider

    async def execute(self, rating_key: str, user_token: str) -> None:
        return await self.provider.add_item(rating_key, user_token)
