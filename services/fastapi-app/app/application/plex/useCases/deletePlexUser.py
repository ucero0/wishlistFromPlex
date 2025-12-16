"""use case for deleting a Plex user."""
from app.domain.ports.repositories.plex.plexUserRepo import PlexUserRepoPort
from app.domain.models.plexUser import PlexUser

class DeletePlexUserUseCase:
    def __init__(self, repo: PlexUserRepoPort):
        self.repo = repo

    async def execute(self, user: PlexUser) -> PlexUser:
        return await self.repo.delete_user(user)
