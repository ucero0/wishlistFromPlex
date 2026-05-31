from app.domain.models.tv_episode import TvEpisode
from app.domain.ports.external.tmdb.tmdb_show_catalog_provider import (
    TmdbShowCatalogProvider,
)


class GetTmdbShowCatalogEpisodesQuery:
    def __init__(self, catalog_provider: TmdbShowCatalogProvider):
        self._catalog_provider = catalog_provider

    async def execute(self, tmdb_tv_id: int) -> list[TvEpisode]:
        return await self._catalog_provider.get_show_catalog_episodes(tmdb_tv_id)
