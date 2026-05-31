"""Port for Plex Discover show catalog (seasons/episodes metadata)."""
from typing import Protocol

from app.domain.models.tv_episode import TvEpisode


class PlexDiscoverCatalogProvider(Protocol):
    async def get_show_catalog_episodes(
        self,
        rating_key: str,
        user_token: str,
    ) -> list[TvEpisode]:
        """List episodes Plex Discover metadata knows about for a show."""
        ...
