"""Internal domain models for torrents - pure business logic."""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum


class TorrentStatus(str, Enum):
    """Torrent status enumeration - domain model."""
    QUEUED = "queued"
    DOWNLOADING = "downloading"
    SEEDING = "seeding"
    PAUSED = "paused"
    CHECKING = "checking"
    ERROR = "error"
    COMPLETED = "completed"
    REMOVED = "removed"


class Torrent(BaseModel):
    """Internal domain model for a torrent."""
    guid_plex: str
    torrent_hash: str
    name: Optional[str] = None
    status: TorrentStatus = TorrentStatus.QUEUED
    progress: float = 0.0
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
    added_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

