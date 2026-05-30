"""use case for updating a Plex user."""
from typing import Optional

from app.application.plex.queries.get_watchlist_query import GetWatchlistQuery
from app.domain.models.plex_user import PlexUser
from app.domain.ports.repositories.plex.plex_user_repository_port import PlexUserRepoPort


class UpdatePlexUserUseCase:
    def __init__(
        self,
        repo: PlexUserRepoPort,
        get_watchlist_query: GetWatchlistQuery,
    ):
        self.repo = repo
        self._get_watchlist_query = get_watchlist_query

    async def execute(self, user: PlexUser) -> Optional[PlexUser]:
        if user.plex_token:
            await self._get_watchlist_query.execute(user.plex_token)
        return await self.repo.update_user(user)
