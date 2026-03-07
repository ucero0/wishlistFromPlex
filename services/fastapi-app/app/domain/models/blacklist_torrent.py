"""Domain model for blacklisted torrents (e.g. infected, unhealthy)."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class BlacklistTorrent(BaseModel):
    """A torrent blacklisted by Prowlarr GUID so it is not sent to Deluge again."""

    id: Optional[int] = None
    guid_prowlarr: str
    reason: str  # e.g. "infected", "unhealthy"
    name: Optional[str] = None  # Media title/name for display
    year: Optional[int] = None
    type: Optional[str] = None  # "movie" or "show"
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
