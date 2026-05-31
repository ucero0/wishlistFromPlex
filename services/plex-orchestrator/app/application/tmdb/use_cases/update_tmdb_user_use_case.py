from app.application.tmdb.queries.get_tmdb_watchlist_query import GetTmdbWatchlistQuery
from app.domain.models.tmdb_user import TmdbUser
from app.domain.ports.external.tmdb.tmdb_watchlist_provider import TmdbWatchlistProvider
from app.domain.ports.repositories.tmdb.tmdb_user_repository_port import TmdbUserRepoPort


class UpdateTmdbUserUseCase:
    def __init__(
        self,
        repo: TmdbUserRepoPort,
        watchlist_provider: TmdbWatchlistProvider,
    ):
        self._repo = repo
        self._watchlist_provider = watchlist_provider

    async def execute(self, user: TmdbUser) -> TmdbUser | None:
        if user.access_token:
            account_id = await self._watchlist_provider.get_account_id(user.access_token)
            user = user.model_copy(update={"account_id": account_id})
            await GetTmdbWatchlistQuery(self._watchlist_provider).execute(
                user.account_id, user.access_token
            )
        return await self._repo.update_user(user)
