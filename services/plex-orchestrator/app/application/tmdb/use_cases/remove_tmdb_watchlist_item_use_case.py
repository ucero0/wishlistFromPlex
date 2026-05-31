from app.domain.ports.external.tmdb.tmdb_watchlist_provider import TmdbWatchlistProvider


class RemoveTmdbWatchlistItemUseCase:
    def __init__(self, provider: TmdbWatchlistProvider):
        self._provider = provider

    async def execute(
        self,
        account_id: int,
        access_token: str,
        media_type: str,
        media_id: int,
    ) -> None:
        await self._provider.remove_from_watchlist(
            account_id, access_token, media_type, media_id
        )
