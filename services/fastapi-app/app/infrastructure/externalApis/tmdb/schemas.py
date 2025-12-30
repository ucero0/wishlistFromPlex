"""External schemas for TMDB API."""
from pydantic import BaseModel
from typing import Optional, List

class TMDBMovieResponse(BaseModel):
    """TMDB movie response schema."""
    id: int
    title: str
    original_title: str
    original_language: str
    release_date: Optional[str] = None

class TMDBTVResponse(BaseModel):
    """TMDB TV show response schema."""
    id: int
    name: str
    original_name: str
    original_language: str
    first_air_date: Optional[str] = None

class TMDBMovieSearchResult(BaseModel):
    """TMDB movie search result schema."""
    id: int
    title: str
    original_title: str
    original_language: str
    release_date: Optional[str] = None

class TMDBTVSearchResult(BaseModel):
    """TMDB TV show search result schema."""
    id: int
    name: str
    original_name: str
    original_language: str
    first_air_date: Optional[str] = None

class TMDBMovieSearchResponse(BaseModel):
    """TMDB movie search response schema."""
    results: List[TMDBMovieSearchResult]

class TMDBTVSearchResponse(BaseModel):
    """TMDB TV show search response schema."""
    results: List[TMDBTVSearchResult]

