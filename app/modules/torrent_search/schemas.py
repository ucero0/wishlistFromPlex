"""Torrent search module Pydantic schemas."""
from __future__ import annotations
import logging

from pydantic import BaseModel, Field, model_validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class SearchStatusEnum(str, Enum):
    """Search status for API responses."""
    PENDING = "pending"
    SEARCHING = "searching"
    FOUND = "found"
    NOT_FOUND = "not_found"
    ADDED = "added"
    ERROR = "error"


class QualityInfo(BaseModel):
    """Quality information for a torrent."""
    resolution: Optional[str] = None  # 2160p, 1080p, 720p, etc.
    audio: Optional[str] = None  # TrueHD, DTS-HD MA, Atmos, etc.
    video_codec: Optional[str] = None  # x265, x264, HEVC, etc.
    hdr: Optional[str] = None  # HDR10, Dolby Vision, HDR10+, etc.
    source: Optional[str] = None  # BluRay, WEB-DL, HDTV, etc.
    release_group: Optional[str] = None





class SearchRequest(BaseModel):
    """Request to search for torrents using rating_key (backward compatibility)."""
    rating_key: str = Field(..., description="Plex rating_key for the wishlist item")
    force: bool = Field(default=False, description="Force new search even if already searched")


class SearchByQueryRequest(BaseModel):
    """Request to search for torrents using a query string."""
    query: str = Field(..., description="Search query string (e.g., 'The Matrix 1999')")
    media_type: str = Field(default="movie", description="Media type: 'movie' or 'tv'")
    rating_key: Optional[str] = Field(default=None, description="Optional rating_key for database tracking")
    auto_add_to_deluge: bool = Field(default=True, description="Automatically add best match to Deluge")
    force: bool = Field(default=False, description="Force new search even if already searched")


class SearchResponse(BaseModel):
    """Response from search operation."""
    rating_key: str
    status: SearchStatusEnum
    search_query: Optional[str] = None
    results_count: int = 0
    best_match: Optional[TorrentResult] = None
    all_results: List[TorrentResult] = []
    torrent_hash: Optional[str] = None
    message: str


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


class ProwlarrStatusResponse(BaseModel):
    """Prowlarr connection status."""
    connected: bool
    version: Optional[str] = None
    indexer_count: int = 0
    error: Optional[str] = None


class ProwlarrRawResult(BaseModel):
    """Raw result from Prowlarr API."""
    title: str
    indexer: str = "Unknown"
    size: Optional[int] = 0
    seeders: Optional[int] = Field(default=0)
    leechers: Optional[int] = 0
    magnetUrl: Optional[str] = None
    downloadUrl: Optional[str] = None
    infoUrl: Optional[str] = None
    publishDate: Optional[datetime] = None
    guid: Optional[str] = None
    indexerId: Optional[int] = None
    protocol: Optional[str] = None  # Download protocol (torrent, magnet, etc.)
    

    @model_validator(mode='before')
    @classmethod
    def normalize_seeders_field(cls, data: Any) -> Any:
        """Normalize seeders field from different possible field names."""
        if isinstance(data, dict):
            # Handle different field names for seeders (seeders, seedCount, seeds)
            if "seeders" not in data or data.get("seeders") is None:
                if "seedCount" in data:
                    data["seeders"] = data.get("seedCount", 0)
                elif "seeds" in data:
                    data["seeders"] = data.get("seeds", 0)
        return data
    
    class Config:
        populate_by_name = True  # Allow both field name and alias
        extra = "ignore"  # Ignore extra fields from Prowlarr

class TorrentResult(ProwlarrRawResult):
    """Processed torrent search result with quality scoring."""
    # Base fields from ProwlarrRawResult (using snake_case for API consistency)
    
    quality_score: int  # Computed quality score
    quality_info: QualityInfo  # Parsed quality information
    