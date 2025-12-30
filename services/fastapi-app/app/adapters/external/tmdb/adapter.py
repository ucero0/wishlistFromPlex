"""Adapter for TMDB - bridges infrastructure and domain."""
import logging
from typing import Optional, Tuple
from app.domain.ports.external.tmdb.tmdbProvider import TMDBProvider
from app.infrastructure.externalApis.tmdb.client import TMDBClient

logger = logging.getLogger(__name__)


class TMDBAdapter(TMDBProvider):
    """Adapter that converts TMDB infrastructure to domain models."""
    
    def __init__(self, client: TMDBClient):
        self.client = client
    
    async def get_original_title_and_language(
        self, 
        title: str, 
        year: int, 
        media_type: str
    ) -> Optional[Tuple[str, str]]:
        """
        Get original title and original language from TMDB by searching.
        
        Args:
            title: The title to search for
            year: The release year
            media_type: "movie" or "show"
            
        Returns:
            Tuple of (original_title, original_language) if found, None otherwise
        """
        # Check if client has a valid API key (check if it's empty)
        api_key = getattr(self.client, 'api_key', None)
        if not api_key or (isinstance(api_key, str) and api_key.strip() == ""):
            logger.warning(f"TMDB API key is not configured, skipping search for {title} ({year})")
            return None
        
        try:
            logger.info(f"Searching TMDB for {media_type}: {title} ({year})")
            response = await self.client.search(
                title=title,
                year=year,
                media_type=media_type
            )
            
            if response:
                if media_type == "movie":
                    return (response.original_title, response.original_language)
                else:  # show
                    return (response.original_name, response.original_language)
        except Exception as e:
            logger.error(f"Error getting original title from TMDB for {title} ({year}): {e}")
        
        return None

