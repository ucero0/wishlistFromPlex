"""TMDB client - infrastructure layer."""
import logging
import httpx
from typing import Optional, Union
from app.infrastructure.externalApis.tmdb.schemas import (
    TMDBMovieResponse, 
    TMDBTVResponse,
    TMDBMovieSearchResponse,
    TMDBTVSearchResponse
)

logger = logging.getLogger(__name__)

TMDB_API_BASE = "https://api.themoviedb.org/3"

class TMDBClient:
    """Infrastructure client for TMDB API."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = TMDB_API_BASE
    
    async def get_movie(self, tmdb_id: int) -> Optional[TMDBMovieResponse]:
        """
        Get movie details from TMDB API.
        
        Args:
            tmdb_id: The TMDB movie ID
            
        Returns:
            TMDBMovieResponse if successful, None otherwise
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.base_url}/movie/{tmdb_id}",
                    params={"api_key": self.api_key},
                )
                response.raise_for_status()
                return TMDBMovieResponse(**response.json())
        except Exception as e:
            logger.error(f"Error fetching movie from TMDB: {e}")
            return None
    
    async def get_tv_show(self, tmdb_id: int) -> Optional[TMDBTVResponse]:
        """
        Get TV show details from TMDB API.
        
        Args:
            tmdb_id: The TMDB TV show ID
            
        Returns:
            TMDBTVResponse if successful, None otherwise
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.base_url}/tv/{tmdb_id}",
                    params={"api_key": self.api_key},
                )
                response.raise_for_status()
                return TMDBTVResponse(**response.json())
        except Exception as e:
            logger.error(f"Error fetching TV show from TMDB: {e}")
            return None
    
    async def search(self, title: str, year: Optional[int] = None, media_type: str = "movie") -> Optional[Union[TMDBMovieResponse, TMDBTVResponse]]:
        """
        Search for a movie or TV show by title, year, and type.
        
        Args:
            title: The title to search for
            year: Optional year to filter results (release_date for movies, first_air_date for TV)
            media_type: "movie" or "show"
            
        Returns:
            TMDBMovieResponse or TMDBTVResponse if found, None otherwise
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                params = {
                    "api_key": self.api_key,
                    "query": title,
                }
                
                if media_type == "movie":
                    endpoint = f"{self.base_url}/search/movie"
                    if year:
                        params["year"] = year
                else:  # show
                    endpoint = f"{self.base_url}/search/tv"
                    if year:
                        params["first_air_date_year"] = year
                
                response = await client.get(endpoint, params=params)
                response.raise_for_status()
                
                if media_type == "movie":
                    search_response = TMDBMovieSearchResponse(**response.json())
                    if search_response.results:
                        return await self.get_movie(search_response.results[0].id)
                else:  # show
                    search_response = TMDBTVSearchResponse(**response.json())
                    if search_response.results:
                        return await self.get_tv_show(search_response.results[0].id)
                
                return None
        except Exception as e:
            logger.error(f"Error searching {media_type} in TMDB: {e}")
            return None

