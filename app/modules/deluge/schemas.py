"""Deluge module Pydantic schemas."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class TorrentStatusEnum(str, Enum):
    """Torrent status for API responses."""
    QUEUED = "queued"
    DOWNLOADING = "downloading"
    SEEDING = "seeding"
    PAUSED = "paused"
    CHECKING = "checking"
    ERROR = "error"
    COMPLETED = "completed"
    REMOVED = "removed"


# =============================================================================
# Request Schemas
# =============================================================================

class AddTorrentRequest(BaseModel):
    """Request to add a torrent via magnet link."""
    rating_key: str = Field(..., description="Plex rating_key to associate with this torrent")
    magnet_link: str = Field(..., description="Magnet link for the torrent")
    
    class Config:
        json_schema_extra = {
            "example": {
                "rating_key": "5d776d1847dd6e001f6f002f",
                "magnet_link": "magnet:?xt=urn:btih:..."
            }
        }


class RemoveTorrentRequest(BaseModel):
    """Request to remove a torrent."""
    remove_data: bool = Field(default=False, description="Also delete downloaded files")
    
    class Config:
        json_schema_extra = {
            "example": {
                "remove_data": False
            }
        }


# =============================================================================
# Response Schemas
# =============================================================================

class TorrentItemResponse(BaseModel):
    """Torrent item response."""
    id: int
    rating_key: str
    torrent_hash: str
    magnet_link: Optional[str] = None
    name: Optional[str] = None
    status: TorrentStatusEnum
    progress: float
    total_size: Optional[int] = None
    downloaded: int = 0
    uploaded: int = 0
    download_speed: int = 0
    upload_speed: int = 0
    save_path: Optional[str] = None
    num_seeds: int = 0
    num_peers: int = 0
    ratio: float = 0.0
    eta: int = -1
    added_at: datetime
    completed_at: Optional[datetime] = None
    last_updated: datetime

    class Config:
        from_attributes = True


class TorrentInfoResponse(BaseModel):
    """Detailed torrent info from Deluge daemon."""
    torrent_hash: str
    name: str
    state: str
    progress: float
    total_size: int
    downloaded: int
    uploaded: int
    download_speed: int
    upload_speed: int
    save_path: str
    num_seeds: int
    num_peers: int
    ratio: float
    eta: int
    is_finished: bool
    paused: bool
    
    class Config:
        json_schema_extra = {
            "example": {
                "torrent_hash": "abc123...",
                "name": "Movie.2024.1080p.BluRay",
                "state": "Downloading",
                "progress": 45.5,
                "total_size": 2147483648,
                "downloaded": 976744448,
                "uploaded": 104857600,
                "download_speed": 5242880,
                "upload_speed": 1048576,
                "save_path": "/downloads",
                "num_seeds": 15,
                "num_peers": 3,
                "ratio": 0.1,
                "eta": 3600,
                "is_finished": False,
                "paused": False
            }
        }


class AddTorrentResponse(BaseModel):
    """Response after adding a torrent."""
    success: bool
    message: str
    torrent_hash: Optional[str] = None
    torrent: Optional[TorrentItemResponse] = None


class RemoveTorrentResponse(BaseModel):
    """Response after removing a torrent."""
    success: bool
    message: str
    torrent_hash: str
    data_removed: bool = False


class TorrentListResponse(BaseModel):
    """Response for list of torrents."""
    total: int
    torrents: list[TorrentItemResponse]


class DelugeStatusResponse(BaseModel):
    """Deluge daemon connection status."""
    connected: bool
    daemon_version: Optional[str] = None
    error: Optional[str] = None

