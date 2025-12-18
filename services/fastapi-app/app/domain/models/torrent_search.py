"""Torrent search domain models - pure domain concepts only."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class SearchStatusEnum(str, Enum):
    """Search status enum - domain concept."""
    PENDING = "pending"
    SEARCHING = "searching"
    FOUND = "found"
    NOT_FOUND = "not_found"
    ADDED = "added"
    ERROR = "error"


class QualityInfo(BaseModel):
    """Quality information for a torrent - domain value object."""
    resolution: Optional[str] = None  # 2160p, 1080p, 720p, etc.
    audio: Optional[str] = None  # TrueHD, DTS-HD MA, Atmos, etc.
    video_codec: Optional[str] = None  # x265, x264, HEVC, etc.
    hdr: Optional[str] = None  # HDR10, Dolby Vision, HDR10+, etc.
    source: Optional[str] = None  # BluRay, WEB-DL, HDTV, etc.
    release_group: Optional[str] = None


class TorrentSearchResult(BaseModel):
    """Processed torrent search result with quality scoring."""
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
    protocol: Optional[str] = None
    quality_score: int  # Computed quality score
    quality_info: QualityInfo  # Parsed quality information

