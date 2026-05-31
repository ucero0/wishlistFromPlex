from typing import Protocol

from app.domain.models.tv_episode import TvEpisode


class TmdbShowCatalogProvider(Protocol):
    async def get_show_catalog_episodes(self, tmdb_tv_id: int) -> list[TvEpisode]: ...
