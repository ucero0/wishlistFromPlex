from app.domain.models.media import MediaItem
from app.domain.ports.external.tmdb.tmdb_watchlist_provider import TmdbWatchlistProvider


class GetTmdbWatchlistQuery:
    def __init__(self, provider: TmdbWatchlistProvider):
        self._provider = provider

    async def execute(self, account_id: int, access_token: str) -> list[MediaItem]:
        return await self._provider.get_watchlist(account_id, access_token)
