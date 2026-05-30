"""Schemas for blacklist torrent API."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AddToBlacklistRequest(BaseModel):
    """Request to add a torrent to the blacklist (do not send to Deluge again)."""
    guid_prowlarr: str
    reason: str  # e.g. "infected", "unhealthy"
    name: Optional[str] = None  # Media title for display
    year: Optional[int] = None
    type: Optional[str] = None  # "movie" or "show"


class AddToBlacklistByHashRequest(BaseModel):
    """Request to add a torrent to the blacklist by its hash (uid from torrent download DB)."""
    torrent_hash: str  # UID in active_downloads (same as used in antivirus scan)
    reason: str  # e.g. "infected", "unhealthy"


class AddToBlacklistResponse(BaseModel):
    """Response after adding to blacklist."""
    guid_prowlarr: str
    reason: str
    id: int
    name: Optional[str] = None
    year: Optional[int] = None
    type: Optional[str] = None


class BlacklistTorrentItem(BaseModel):
    """Single blacklist entry (for list and get)."""
    id: int
    guid_prowlarr: str
    reason: str
    name: Optional[str] = None
    year: Optional[int] = None
    type: Optional[str] = None
    created_at: Optional[datetime] = None


class BlacklistTorrentListResponse(BaseModel):
    """Response for list blacklist: list of entries."""
    items: list[BlacklistTorrentItem]
    total: int
