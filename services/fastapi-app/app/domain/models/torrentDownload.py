"""Domain model for torrent downloads."""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class TorrentDownload(BaseModel):
    """Domain model for a torrent download item."""
    id: Optional[int] = None
    guidPlex: str
    ratingKey: Optional[str] = None  # Plex ratingKey for adding back to watchlist
    plexUserToken: Optional[str] = None  # Plex user token for adding back to watchlist
    guidProwlarr: str
    uid: str
    title: str
    fileName: Optional[str] = None  # File name from Deluge
    year: Optional[int] = None
    type: str  # "movie" or "show"
    season: Optional[int] = None
    episode: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

