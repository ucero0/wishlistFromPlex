"""Fetch episode catalog for a watchlisted show (Plex first, TMDB fallback)."""
import logging

from app.application.plex.queries.get_plex_discover_show_catalog_episodes_query import (
    GetPlexDiscoverShowCatalogEpisodesQuery,
)
from app.application.plex.queries.get_plex_server_show_catalog_episodes_query import (
    GetPlexServerShowCatalogEpisodesQuery,
)
from app.application.pipelines.watchlist.services.show_watchlist_helpers import (
    discover_rating_key_for_show,
)
from app.application.tmdb.queries.get_tmdb_show_catalog_episodes_query import (
    GetTmdbShowCatalogEpisodesQuery,
)
from app.application.tmdb.queries.resolve_tmdb_tv_id_for_show_query import (
    ResolveTmdbTvIdForShowQuery,
)
from app.domain.models.media import MediaItem
from app.domain.models.tv_episode import TvEpisode
from app.domain.services.tmdb_guid import parse_tmdb_guid

logger = logging.getLogger(__name__)


class GetShowCatalogEpisodesQuery:
    def __init__(
        self,
        plex_discover_catalog_query: GetPlexDiscoverShowCatalogEpisodesQuery,
        plex_server_catalog_query: GetPlexServerShowCatalogEpisodesQuery,
        resolve_tmdb_tv_id_query: ResolveTmdbTvIdForShowQuery,
        tmdb_catalog_query: GetTmdbShowCatalogEpisodesQuery,
    ):
        self._plex_discover_catalog_query = plex_discover_catalog_query
        self._plex_server_catalog_query = plex_server_catalog_query
        self._resolve_tmdb_tv_id_query = resolve_tmdb_tv_id_query
        self._tmdb_catalog_query = tmdb_catalog_query

    async def execute(
        self,
        watchlist: MediaItem,
        user_token: str,
        *,
        plex_user_token: str | None = None,
    ) -> list[TvEpisode]:
        is_tmdb_source = parse_tmdb_guid(watchlist.guid or "") is not None

        discover_key = discover_rating_key_for_show(watchlist)
        if discover_key and user_token and not is_tmdb_source:
            episodes = await self._plex_discover_catalog_query.execute(
                discover_key, user_token
            )
            if episodes:
                logger.info(
                    "Using Plex Discover catalog for '%s' (%s episodes)",
                    watchlist.title,
                    len(episodes),
                )
                return episodes

        if is_tmdb_source:
            tmdb_tv_id = await self._resolve_tmdb_tv_id_query.execute(
                watchlist, user_token
            )
            if tmdb_tv_id is None:
                logger.warning(
                    "No TMDB episode catalog for show '%s' (guid=%s)",
                    watchlist.title,
                    watchlist.guid,
                )
                return []
            episodes = await self._tmdb_catalog_query.execute(tmdb_tv_id)
            if episodes:
                logger.info(
                    "Using TMDB catalog for '%s' (%s episodes)",
                    watchlist.title,
                    len(episodes),
                )
            return episodes

        library_guid = watchlist.plex_library_guid
        if library_guid:
            episodes = await self._plex_server_catalog_query.execute(library_guid)
            if episodes:
                logger.info(
                    "Using Plex server catalog for '%s' (%s episodes)",
                    watchlist.title,
                    len(episodes),
                )
                return episodes

        if watchlist.guid and parse_tmdb_guid(watchlist.guid) is None:
            episodes = await self._plex_server_catalog_query.execute(watchlist.guid)
            if episodes:
                logger.info(
                    "Using Plex server catalog for '%s' (%s episodes)",
                    watchlist.title,
                    len(episodes),
                )
                return episodes

        tmdb_tv_id = await self._resolve_tmdb_tv_id_query.execute(
            watchlist, user_token
        )
        if tmdb_tv_id is None:
            logger.warning(
                "No Plex or TMDB episode catalog for show '%s' (guid=%s)",
                watchlist.title,
                watchlist.guid,
            )
            return []

        episodes = await self._tmdb_catalog_query.execute(tmdb_tv_id)
        if episodes:
            logger.info(
                "Using TMDB catalog for '%s' (%s episodes)",
                watchlist.title,
                len(episodes),
            )
        return episodes
