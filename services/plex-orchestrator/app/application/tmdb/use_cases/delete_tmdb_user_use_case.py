from app.domain.models.tmdb_user import TmdbUser
from app.domain.ports.repositories.tmdb.tmdb_user_repository_port import TmdbUserRepoPort


class DeleteTmdbUserUseCase:
    def __init__(self, repo: TmdbUserRepoPort):
        self._repo = repo

    async def execute(self, user: TmdbUser) -> TmdbUser | None:
        return await self._repo.delete_user(user)
