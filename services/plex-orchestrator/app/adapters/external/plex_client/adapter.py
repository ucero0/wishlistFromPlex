from typing import List

from app.adapters.external.plex_client.mapper import to_domain
from app.domain.models.media import MediaItem
from app.domain.models.tv_episode import TvEpisode
from app.domain.ports.external.plex.plex_discover_catalog_provider import (
    PlexDiscoverCatalogProvider,
)
from app.domain.ports.external.plex.plex_discover_metadata_provider import (
    PlexDiscoverMetadataProvider,
)
from app.domain.ports.external.plex.plex_watchlist_provider import PlexWatchlistProvider
from app.infrastructure.external_apis.plex.plex_client.client import PlexWatchlistClient
from app.infrastructure.external_apis.plex.plex_client.schemas import PlexWatchlistItemDTO


class PlexWatchlistAdapter(
    PlexWatchlistProvider,
    PlexDiscoverMetadataProvider,
    PlexDiscoverCatalogProvider,
):
    """Adapter for Plex watchlist."""
    def __init__(self, client: PlexWatchlistClient):
        self.client = client

    async def get_watchlist(self, user_token: str) -> List[MediaItem]:
        raw = await self.client.get_watchlist_raw(user_token)
        items = raw.get("MediaContainer", {}).get("Metadata", [])
        dtos = [PlexWatchlistItemDTO(**item) for item in items]
        return [to_domain(dto) for dto in dtos]

    async def add_item(self, rating_key: str, user_token: str) -> None:
        await self.client.add_item_raw(rating_key, user_token)

    async def delete_item(self, rating_key: str, user_token: str) -> None:
        await self.client.delete_item_raw(rating_key, user_token)

    async def get_metadata_guids(
        self,
        rating_key: str,
        user_token: str,
    ) -> list[str]:
        raw = await self.client.get_metadata_raw(rating_key, user_token)
        metadata = raw.get("MediaContainer", {}).get("Metadata") or []
        if not metadata:
            return []
        guids: list[str] = []
        for entry in metadata[0].get("Guid") or []:
            if isinstance(entry, dict):
                guid = entry.get("id")
                if guid:
                    guids.append(str(guid))
            elif entry:
                guids.append(str(entry))
        return guids

    async def get_show_catalog_episodes(
        self,
        rating_key: str,
        user_token: str,
    ) -> List[TvEpisode]:
        from app.adapters.external.plex.tv_episode_mapper import (
            crawl_show_episodes_from_discover,
        )

        episodes: List[TvEpisode] = await crawl_show_episodes_from_discover(
            self.client, rating_key, user_token
        )
        return sorted(episodes, key=lambda ep: (ep.season, ep.episode))

