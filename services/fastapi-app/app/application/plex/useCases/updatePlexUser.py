"""use case for updating a Plex user."""
from app.domain.ports.repositories.plex.plexUserRepo import PlexUserRepoPort
from app.domain.models.plexUser import PlexUser
from typing import Optional

class UpdatePlexUserUseCase:
    def __init__(self, repo: PlexUserRepoPort):
        self.repo = repo

    async def execute(self, user: PlexUser) -> Optional[PlexUser]:
        return await self.repo.update_user(user)
