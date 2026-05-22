"""Plex library folder paths persisted from the Plex server API."""
from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel

PlexLibraryPathMediaType = Literal["movie", "tvshow", "other"]


class PlexLibraryPath(BaseModel):
    """One root folder configured on a Plex library section."""

    id: Optional[int] = None
    section_id: str
    section_title: str
    media_type: PlexLibraryPathMediaType
    path: str
    is_active: bool = True
    last_synced_at: Optional[datetime] = None
    volume_root: Optional[str] = None
    total_bytes: Optional[int] = None
    used_bytes: Optional[int] = None
    free_bytes: Optional[int] = None
    used_percent: Optional[float] = None
    disk_stats_synced_at: Optional[datetime] = None
    disk_stats_error: Optional[str] = None
