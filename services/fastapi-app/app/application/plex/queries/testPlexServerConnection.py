"""Query for testing Plex server connectivity."""
from app.domain.models.external_connection import ExternalConnectionStatus
from app.domain.ports.external.plex.plexServerLibraryProvider import PlexServerLibraryProvider


class TestPlexServerConnectionQuery:
    def __init__(self, provider: PlexServerLibraryProvider):
        self.provider = provider

    async def execute(self) -> ExternalConnectionStatus:
        return await self.provider.test_connection()
