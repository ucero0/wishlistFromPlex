"""Internal domain models for torrents - pure business logic."""
from pydantic import BaseModel
from typing import Optional, List
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
    hash: str
    fileName: str
    state: str
    progress: float = 0.0
    total_size: Optional[int] = None
    download_speed: int = 0
    eta: Optional[int] = None
    time_added: Optional[float] = None  # Unix timestamp when torrent was added


class ListTorrents(BaseModel):
    """List of torrents."""
    torrents: List[Torrent]