"""Factory for TMDB queries."""
import logging
from app.application.tmdb.queries.getOriginalTitle import GetOriginalTitleFromTMDBQuery
from app.application.tmdb.queries.testTmdbConnection import TestTmdbConnectionQuery
from app.infrastructure.externalApis.tmdb.client import TMDBClient
from app.adapters.external.tmdb.adapter import TMDBAdapter
from app.core.config import settings

logger = logging.getLogger(__name__)

def _create_tmdb_adapter() -> TMDBAdapter:
    api_key = settings.tmdb_api_key or ""
    return TMDBAdapter(TMDBClient(api_key=api_key))


def create_test_tmdb_connection_query() -> TestTmdbConnectionQuery:
    return TestTmdbConnectionQuery(_create_tmdb_adapter())


def create_get_original_title_from_tmdb_query() -> GetOriginalTitleFromTMDBQuery:
    """Factory function to create GetOriginalTitleFromTMDBQuery with proper dependency injection."""
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
    return GetOriginalTitleFromTMDBQuery(tmdb_provider=_create_tmdb_adapter())

