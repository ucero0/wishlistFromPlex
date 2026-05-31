"""Load a TV show episode catalog from Plex Discover."""
from app.domain.ports.external.plex.plex_discover_catalog_provider import (
    PlexDiscoverCatalogProvider,
)


class GetPlexDiscoverShowCatalogEpisodesQuery:
    def __init__(self, catalog_provider: PlexDiscoverCatalogProvider):
        self._catalog_provider = catalog_provider

    async def execute(self, rating_key: str, user_token: str) -> list:
        return await self._catalog_provider.get_show_catalog_episodes(
            rating_key, user_token
        )
