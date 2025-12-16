"""use case for updating a Plex user."""
from app.domain.ports.repositories.plex.plexUserRepo import PlexUserRepoPort
from app.domain.models.plexUser import PlexUser

class UpdatePlexUserUseCase:
    def __init__(self, repo: PlexUserRepoPort):
        self.repo = repo

    async def execute(self, user: PlexUser) -> PlexUser:
        return await self.repo.update_user(user)
