"""Internal domain models for torrents - pure business logic."""
from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


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

    model_config = ConfigDict(from_attributes=False)

    hash: str
    file_name: str
    state: str
    progress: float = 0.0
    total_size: Optional[int] = None
    download_speed: int = 0
    eta: Optional[int] = None
    time_added: Optional[float] = None  # Unix timestamp when torrent was added

    @property
    def is_finished(self) -> bool:
        """True when Deluge reports the download as complete (not actively downloading)."""
        progress = float(self.progress or 0)
        if progress >= 99.9:
            return True
        state = (self.state or "").lower()
        return state in ("seeding", "paused", "checking", "queued")


class ListTorrents(BaseModel):
    """List of torrents."""

    torrents: List[Torrent]
