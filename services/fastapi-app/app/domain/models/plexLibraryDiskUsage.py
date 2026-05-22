"""Plex library folder paths enriched with volume and disk usage (from this host)."""
from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel

from app.domain.models.plexLibraryLocations import PlexLibrarySectionMediaKind


class PlexLibraryPathDiskInfo(BaseModel):
    """One Plex library root path plus volume id and space, when visible from this process."""

    path: str
    volume_root: Optional[str] = None
    total_bytes: Optional[int] = None
    used_bytes: Optional[int] = None
    free_bytes: Optional[int] = None
    used_percent: Optional[float] = None
    error: Optional[str] = None


class PlexLibrarySectionDiskUsage(BaseModel):
    """Library section with per-folder disk information."""

    section_id: str
    section_title: str
    media_type: PlexLibrarySectionMediaKind
    locations: List[PlexLibraryPathDiskInfo]


class PlexLibraryLocationsDiskUsage(BaseModel):
    """All movie/TV sections with disk stats for each configured path."""

    sections: List[PlexLibrarySectionDiskUsage]
