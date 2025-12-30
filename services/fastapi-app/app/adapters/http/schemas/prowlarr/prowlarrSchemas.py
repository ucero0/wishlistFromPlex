"""HTTP request/response schemas for Prowlarr torrent search endpoints."""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.domain.models.torrent_search import (
    SearchStatusEnum,
    TorrentSearchResult,
)


class SearchRequest(BaseModel):
    """Request to search for torrents using rating_key (backward compatibility)."""
    rating_key: str = Field(..., description="Plex rating_key for the wishlist item")


class SearchByQueryRequest(BaseModel):
    """Request to search for torrents using a query string."""
    query: str = Field(..., description="Search query string (e.g., 'The Matrix 1999')")
    media_type: str = Field(default="movie", description="Media type: 'movie' or 'tv'")
    rating_key: Optional[str] = Field(default=None, description="Optional rating_key for database tracking")
    auto_add_to_deluge: bool = Field(default=True, description="Automatically add best match to Deluge")


class SearchResponse(BaseModel):
    """Response from search operation."""
    title: str
    indexer: str
    sizeGb: float
    seeders: int
    leechers: int


class SearchResultResponse(BaseModel):
    """Full search result from database."""
    id: int
    rating_key: str
    status: SearchStatusEnum
    search_query: Optional[str] = None
    selected_torrent_title: Optional[str] = None
    selected_torrent_indexer: Optional[str] = None
    selected_torrent_size: Optional[float] = None
    selected_torrent_seeders: Optional[int] = None
    selected_torrent_quality_score: Optional[int] = None
    quality_info: Optional[Dict[str, Any]] = None
    torrent_hash: Optional[str] = None
    searched_at: Optional[datetime] = None
    added_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class SearchStatsResponse(BaseModel):
    """Search statistics."""
    total_searches: int
    found: int
    not_found: int
    added: int
    errors: int
    pending: int


class ProwlarrConnectionResponse(BaseModel):
    """Response for Prowlarr connection test."""
    connected: bool
    version: Optional[str] = None
    error: Optional[str] = None


class ProwlarrIndexerCountResponse(BaseModel):
    """Response for Prowlarr indexer count."""
    count: int

