"""TMDB user queries."""
from app.domain.models.tmdb_user import TmdbUser
from app.domain.ports.repositories.tmdb.tmdb_user_repository_port import TmdbUserRepoPort


class GetTmdbUserQuery:
    def __init__(self, repo: TmdbUserRepoPort):
        self._repo = repo

    async def execute(self) -> list[TmdbUser]:
        return await self._repo.get_active_users()


class GetTmdbUserByIdQuery:
    def __init__(self, repo: TmdbUserRepoPort):
        self._repo = repo

    async def execute(self, user_id: int) -> TmdbUser | None:
        return await self._repo.get_user_by_id(user_id)


class GetTmdbUserByNameQuery:
    def __init__(self, repo: TmdbUserRepoPort):
        self._repo = repo

    async def execute(self, name: str) -> TmdbUser | None:
        return await self._repo.get_user_by_name(name)
