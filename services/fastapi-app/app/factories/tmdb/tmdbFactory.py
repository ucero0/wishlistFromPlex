"""Factory for TMDB queries."""
import logging
from app.application.tmdb.queries.getOriginalTitle import GetOriginalTitleFromTMDBQuery
from app.infrastructure.externalApis.tmdb.client import TMDBClient
from app.adapters.external.tmdb.adapter import TMDBAdapter
from app.core.config import settings

logger = logging.getLogger(__name__)

def create_get_original_title_from_tmdb_query() -> GetOriginalTitleFromTMDBQuery:
    """Factory function to create GetOriginalTitleFromTMDBQuery with proper dependency injection."""
    # Check if API key is configured
    api_key = settings.tmdb_api_key
    
    if not api_key or (isinstance(api_key, str) and api_key.strip() == ""):
        logger.warning(
            "TMDB API key is not configured. Original title lookup will be disabled. "
            "Set TMDB_API_KEY environment variable in .env file or docker-compose.yml to enable."
        )
        logger.debug(f"Current tmdb_api_key value from settings: {repr(api_key)}")
        # Create a dummy client that will return None for all requests
        tmdb_client = TMDBClient(api_key="")
    else:
        # Log that API key is configured (but don't log the actual key for security)
        logger.info(f"TMDB API key is configured (length: {len(api_key)}). Original title lookup is enabled.")
        tmdb_client = TMDBClient(api_key=api_key)
    
    # Create adapter that implements the port
    tmdb_adapter = TMDBAdapter(client=tmdb_client)
    
    # Query depends on the port, not infrastructure
    return GetOriginalTitleFromTMDBQuery(tmdb_provider=tmdb_adapter)

