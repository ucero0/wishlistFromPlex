"""query for getting all Plex users."""
from app.domain.ports.repositories.plex.plex_user_repository_port import PlexUserRepoPort
from app.domain.models.plex_user import PlexUser
from typing import List, Optional

class GetPlexUserQuery:
    def __init__(self, repo: PlexUserRepoPort):
        self.repo = repo

    async def execute(self) -> List[PlexUser]:
        return await self.repo.get_active_users()

class GetPlexUserByIdQuery:
    def __init__(self, repo: PlexUserRepoPort):
        self.repo = repo

    async def execute(self, user_id: int) -> Optional[PlexUser]:
        return await self.repo.get_user_by_id(user_id)

class GetPlexUserByNameQuery:
    def __init__(self, repo: PlexUserRepoPort):
        self.repo = repo

    async def execute(self, name: str) -> Optional[PlexUser]:
        return await self.repo.get_user_by_name(name)

class GetPlexUserByPlexTokenQuery:
    def __init__(self, repo: PlexUserRepoPort):
        self.repo = repo

    async def execute(self, plex_token: str) -> Optional[PlexUser]:
        return await self.repo.get_user_by_plex_token(plex_token)