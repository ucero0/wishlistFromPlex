"""Composition root for TMDB external integration."""
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.external.tmdb.adapter import TMDBAdapter
from app.adapters.external.tmdb.watchlist_adapter import TmdbWatchlistAdapter
from app.application.pipelines.watchlist.use_cases.remove_watchlist_entry_use_case import (
    RemoveWatchlistEntryUseCase,
)
from app.application.tmdb.queries.get_original_title_query import GetOriginalTitleFromTMDBQuery
from app.application.tmdb.queries.get_tmdb_show_catalog_episodes_query import (
    GetTmdbShowCatalogEpisodesQuery,
)
from app.application.tmdb.queries.resolve_tmdb_tv_id_for_show_query import (
    ResolveTmdbTvIdForShowQuery,
)
from app.composition.plex_external import build_plex_watchlist_adapter
from app.application.tmdb.queries.get_tmdb_watchlist_query import GetTmdbWatchlistQuery
from app.application.tmdb.queries.test_tmdb_connection_query import TestTmdbConnectionQuery
from app.application.tmdb.use_cases.remove_tmdb_watchlist_item_use_case import (
    RemoveTmdbWatchlistItemUseCase,
)
from app.core.config import settings
from app.infrastructure.external_apis.tmdb.client import TMDBClient

logger = logging.getLogger(__name__)


def build_tmdb_client() -> TMDBClient:
    return TMDBClient(api_key=settings.tmdb_api_key or "")


def build_tmdb_adapter() -> TMDBAdapter:
    return TMDBAdapter(build_tmdb_client())


def build_tmdb_watchlist_adapter() -> TmdbWatchlistAdapter:
    return TmdbWatchlistAdapter(build_tmdb_client())


def build_test_tmdb_connection_query() -> TestTmdbConnectionQuery:
    return TestTmdbConnectionQuery(build_tmdb_adapter())


def build_get_original_title_from_tmdb_query() -> GetOriginalTitleFromTMDBQuery:
    api_key = settings.tmdb_api_key
    if not api_key or (isinstance(api_key, str) and api_key.strip() == ""):
        logger.warning(
            "TMDB API key is not configured. Original title lookup will be disabled."
        )
    else:
        logger.info(
            "TMDB API key is configured (length: %s). Original title lookup is enabled.",
            len(api_key),
        )
    return GetOriginalTitleFromTMDBQuery(tmdb_provider=build_tmdb_adapter())


def build_get_tmdb_watchlist_query() -> GetTmdbWatchlistQuery:
    return GetTmdbWatchlistQuery(build_tmdb_watchlist_adapter())


def build_get_tmdb_show_catalog_episodes_query() -> GetTmdbShowCatalogEpisodesQuery:
    return GetTmdbShowCatalogEpisodesQuery(build_tmdb_watchlist_adapter())


def build_resolve_tmdb_tv_id_for_show_query() -> ResolveTmdbTvIdForShowQuery:
    return ResolveTmdbTvIdForShowQuery(
        build_tmdb_client(),
        build_plex_watchlist_adapter(),
    )


def build_remove_tmdb_watchlist_item_use_case() -> RemoveTmdbWatchlistItemUseCase:
    return RemoveTmdbWatchlistItemUseCase(build_tmdb_watchlist_adapter())


def build_remove_watchlist_entry_use_case(
    session: AsyncSession | None = None,
) -> RemoveWatchlistEntryUseCase:
    from app.composition.plex_external import build_remove_watchlist_item_use_case

    _ = session
    return RemoveWatchlistEntryUseCase(
        build_remove_watchlist_item_use_case(),
        build_remove_tmdb_watchlist_item_use_case(),
        build_tmdb_watchlist_adapter(),
    )
