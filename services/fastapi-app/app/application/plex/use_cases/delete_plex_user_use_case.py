"""use case for deleting a Plex user."""
from app.domain.ports.repositories.plex.plex_user_repository_port import PlexUserRepoPort
from app.domain.models.plex_user import PlexUser
from typing import Optional

class DeletePlexUserUseCase:
    def __init__(self, repo: PlexUserRepoPort):
        self.repo = repo

    async def execute(self, user: PlexUser) -> Optional[PlexUser]:
        return await self.repo.delete_user(user)
