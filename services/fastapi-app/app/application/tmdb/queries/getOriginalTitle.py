"""Query to get original title from TMDB by searching."""
import logging
from typing import Optional, Tuple
from app.domain.ports.external.tmdb.tmdbProvider import TMDBProvider
from app.domain.models.media import MediaItem

logger = logging.getLogger(__name__)

class GetOriginalTitleFromTMDBQuery:
    """Query to get original title from TMDB by searching with title and year."""
    
    def __init__(self, tmdb_provider: TMDBProvider):
        self.tmdb_provider = tmdb_provider
    
    async def execute(self, media_item: MediaItem) -> Optional[Tuple[str, str]]:
        """
        Get original title and original language from TMDB by searching with title and year.
        
        Args:
            media_item: The media item with title and year
            
        Returns:
            Tuple of (original_title, original_language) if found, None otherwise
        """
        if not media_item.title or not media_item.year:
            logger.warning(f"Cannot search TMDB: missing title or year for {media_item.guid}")
            return None
        
        if not media_item.type or media_item.type not in ["movie", "show"]:
            logger.warning(f"Invalid media type for TMDB search: {media_item.type}")
            return None
        
        return await self.tmdb_provider.get_original_title_and_language(
            title=media_item.title,
            year=media_item.year,
            media_type=media_item.type
        )

