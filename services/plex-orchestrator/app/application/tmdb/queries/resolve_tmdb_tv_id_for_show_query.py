"""Resolve a TMDB TV show id from a watchlist media item."""
import logging

from app.application.pipelines.watchlist.services.show_watchlist_helpers import (
    discover_rating_key_for_show,
)
from app.domain.errors.tmdb import TMDBConfigurationError
from app.domain.models.media import MediaItem
from app.domain.ports.external.plex.plex_discover_metadata_provider import (
    PlexDiscoverMetadataProvider,
)
from app.domain.services.tmdb_guid import resolve_tmdb_tv_id_from_guid
from app.infrastructure.external_apis.tmdb.client import TMDBClient

logger = logging.getLogger(__name__)


class ResolveTmdbTvIdForShowQuery:
    def __init__(
        self,
        tmdb_client: TMDBClient,
        discover_metadata_provider: PlexDiscoverMetadataProvider,
    ):
        self._tmdb_client = tmdb_client
        self._discover_metadata_provider = discover_metadata_provider

    async def execute(self, watchlist: MediaItem, user_token: str) -> int | None:
        tmdb_id = resolve_tmdb_tv_id_from_guid(watchlist.guid or "")
        if tmdb_id is not None:
            return tmdb_id

        rating_key = discover_rating_key_for_show(watchlist)
        if rating_key and user_token:
            for guid in await self._discover_metadata_provider.get_metadata_guids(
                rating_key, user_token
            ):
                tmdb_id = resolve_tmdb_tv_id_from_guid(guid)
                if tmdb_id is not None:
                    return tmdb_id

        if not watchlist.title:
            logger.warning(
                "Cannot resolve TMDB id for show '%s': missing title",
                watchlist.guid,
            )
            return None

        try:
            result = await self._tmdb_client.search(
                title=watchlist.title,
                year=watchlist.year,
                media_type="tv",
            )
        except TMDBConfigurationError:
            logger.warning(
                "TMDB API key is not configured; cannot resolve show '%s'",
                watchlist.title,
            )
            return None

        if result is None:
            logger.warning(
                "No TMDB match for show '%s' (%s)",
                watchlist.title,
                watchlist.year,
            )
            return None

        logger.info(
            "Resolved TMDB tv/%s for show '%s' via search",
            result.id,
            watchlist.title,
        )
        return result.id
