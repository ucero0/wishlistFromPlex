"""External schemas for TMDB API."""
from pydantic import BaseModel
from typing import Optional, List


class TMDBAccountResponse(BaseModel):
    id: int
    username: Optional[str] = None


class TMDBWatchlistItem(BaseModel):
    id: int
    media_type: Optional[str] = None
    title: Optional[str] = None
    name: Optional[str] = None
    release_date: Optional[str] = None
    first_air_date: Optional[str] = None


class TMDBWatchlistResponse(BaseModel):
    page: int = 1
    total_pages: int = 1
    results: List[TMDBWatchlistItem] = []


class TMDBSeasonEpisode(BaseModel):
    episode_number: int


class TMDBSeasonDetailsResponse(BaseModel):
    season_number: int
    episodes: List[TMDBSeasonEpisode] = []


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
    number_of_seasons: int = 0

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

