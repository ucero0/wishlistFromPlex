"""Query for testing TMDB API connectivity."""
from app.domain.models.external_connection import ExternalConnectionStatus
from app.domain.ports.external.tmdb.tmdb_provider import TMDBProvider


class TestTmdbConnectionQuery:
    def __init__(self, provider: TMDBProvider):
        self.provider = provider

    async def execute(self) -> ExternalConnectionStatus:
        return await self.provider.test_connection()
