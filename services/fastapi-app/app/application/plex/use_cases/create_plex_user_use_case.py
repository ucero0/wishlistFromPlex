"""use case for creating a Plex user."""
from app.application.plex.queries.get_watchlist_query import GetWatchlistQuery
from app.domain.ports.repositories.plex.plex_user_repository_port import PlexUserRepoPort
from app.domain.models.plex_user import PlexUser


class CreatePlexUserUseCase:
    def __init__(
        self,
        repo: PlexUserRepoPort,
        get_watchlist_query: GetWatchlistQuery,
    ):
        self.repo = repo
        self._get_watchlist_query = get_watchlist_query

    async def execute(self, user: PlexUser) -> PlexUser:
        await self._get_watchlist_query.execute(user.plex_token)
        return await self.repo.create_user(user)
