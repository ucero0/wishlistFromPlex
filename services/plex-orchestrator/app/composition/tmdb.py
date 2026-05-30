"""Composition root for TMDB external integration."""
import logging

from app.adapters.external.tmdb.adapter import TMDBAdapter
from app.application.tmdb.queries.get_original_title_query import GetOriginalTitleFromTMDBQuery
from app.application.tmdb.queries.test_tmdb_connection_query import TestTmdbConnectionQuery
from app.core.config import settings
from app.infrastructure.external_apis.tmdb.client import TMDBClient

logger = logging.getLogger(__name__)


def build_tmdb_adapter() -> TMDBAdapter:
    return TMDBAdapter(TMDBClient(api_key=settings.tmdb_api_key or ""))


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
