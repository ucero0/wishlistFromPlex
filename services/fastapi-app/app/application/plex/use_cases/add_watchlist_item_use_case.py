from app.domain.ports.external.plex.plex_watchlist_provider import PlexWatchlistProvider

class AddWatchlistItemUseCase:
    def __init__(self, provider: PlexWatchlistProvider):
        self.provider = provider

    async def execute(self, rating_key: str, user_token: str) -> None:
        return await self.provider.add_item(rating_key, user_token)
