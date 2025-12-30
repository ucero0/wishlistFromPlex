"""TMDB provider port (Protocol)."""
from typing import Protocol, Optional, Tuple

class TMDBProvider(Protocol):
    """Protocol for TMDB movie/TV show information provider."""
    
    async def get_original_title_and_language(
        self, 
        title: str, 
        year: int, 
        media_type: str
    ) -> Optional[Tuple[str, str]]:
        """
        Get original title and original language from TMDB.
        
        Args:
            title: The title to search for
            year: The release year
            media_type: "movie" or "show"
            
        Returns:
            Tuple of (original_title, original_language) if found, None otherwise
        """
        ...

