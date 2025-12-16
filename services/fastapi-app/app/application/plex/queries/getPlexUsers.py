"""query for getting all Plex users."""
from app.domain.ports.repositories.plex.plexUserRepo import PlexUserRepoPort
from app.domain.models.plexUser import PlexUser
from typing import List

class GetPlexUserQuery:
    def __init__(self, repo: PlexUserRepoPort):
        self.repo = repo

    async def execute(self) -> List[PlexUser]:
        return await self.repo.get_active_users()

class GetPlexUserByIdQuery:
    def __init__(self, repo: PlexUserRepoPort):
        self.repo = repo

    async def execute(self, user_id: int) -> PlexUser:
        return await self.repo.get_user_by_id(user_id)

class GetPlexUserByNameQuery:
    def __init__(self, repo: PlexUserRepoPort):
        self.repo = repo

    async def execute(self, name: str) -> PlexUser:
        return await self.repo.get_user_by_name(name)

class GetPlexUserByPlexTokenQuery:
    def __init__(self, repo: PlexUserRepoPort):
        self.repo = repo

    async def execute(self, plex_token: str) -> PlexUser:
        return await self.repo.get_user_by_plex_token(plex_token)