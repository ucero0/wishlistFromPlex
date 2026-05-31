"""TMDB account watchlist and TV catalog adapter."""
import logging

from app.adapters.external.tmdb.watchlist_mapper import watchlist_item_to_media
from app.domain.models.media import MediaItem
from app.domain.models.tv_episode import TvEpisode
from app.domain.ports.external.tmdb.tmdb_show_catalog_provider import (
    TmdbShowCatalogProvider,
)
from app.domain.ports.external.tmdb.tmdb_watchlist_provider import TmdbWatchlistProvider
from app.infrastructure.external_apis.tmdb.client import TMDBClient

logger = logging.getLogger(__name__)


class TmdbWatchlistAdapter(TmdbWatchlistProvider, TmdbShowCatalogProvider):
    def __init__(self, client: TMDBClient):
        self._client = client

    async def get_account_id(self, access_token: str) -> int:
        account = await self._client.get_account(access_token)
        return account.id

    async def get_watchlist(
        self, account_id: int, access_token: str
    ) -> list[MediaItem]:
        raw_items = await self._client.get_watchlist(account_id, access_token)
        items: list[MediaItem] = []
        for raw in raw_items:
            mapped = watchlist_item_to_media(raw)
            if mapped is not None:
                items.append(mapped)
        return items

    async def remove_from_watchlist(
        self,
        account_id: int,
        access_token: str,
        media_type: str,
        media_id: int,
    ) -> None:
        await self._client.remove_from_watchlist(
            account_id, access_token, media_type, media_id
        )

    async def add_to_watchlist(
        self,
        account_id: int,
        access_token: str,
        media_type: str,
        media_id: int,
    ) -> None:
        await self._client.add_to_watchlist(
            account_id, access_token, media_type, media_id
        )

    async def get_show_catalog_episodes(self, tmdb_tv_id: int) -> list[TvEpisode]:
        show = await self._client.get_tv_show(tmdb_tv_id)
        episodes: list[TvEpisode] = []
        for season_number in range(1, max(show.number_of_seasons, 0) + 1):
            season = await self._client.get_tv_season(tmdb_tv_id, season_number)
            for episode in season.episodes:
                episodes.append(
                    TvEpisode(
                        season=season.season_number,
                        episode=episode.episode_number,
                        name=episode.name.strip() if episode.name else None,
                    )
                )
        return sorted(episodes, key=lambda ep: (ep.season, ep.episode))
