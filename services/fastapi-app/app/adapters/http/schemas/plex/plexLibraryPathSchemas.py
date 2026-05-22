"""HTTP schemas for Plex library paths stored in the database."""
from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel

PlexLibraryPathMediaTypeBody = Literal["movie", "tvshow", "other"]


class PlexLibraryPathItem(BaseModel):
    """One row from ``plex_library_paths``."""

    id: int
    section_id: str
    section_title: str
    media_type: PlexLibraryPathMediaTypeBody
    path: str
    is_active: bool
    last_synced_at: Optional[datetime] = None
    volume_root: Optional[str] = None
    total: Optional[str] = None
    used: Optional[str] = None
    free: Optional[str] = None
    used_percent: Optional[float] = None
    disk_stats_synced_at: Optional[datetime] = None
    disk_stats_error: Optional[str] = None


class PlexLibraryServeMetaBody(BaseModel):
    """Refresh outcome returned with library-path read endpoints."""

    plex_sync_attempted: bool = False
    plex_sync_ok: bool = False
    plex_sync_error: Optional[str] = None
    last_synced_at: Optional[datetime] = None
    disk_stats_synced_at: Optional[datetime] = None


class PlexLibraryPathListResponse(PlexLibraryServeMetaBody):
    items: List[PlexLibraryPathItem]
    total: int


class PlexLibraryPathDiskInfoBody(BaseModel):
    """Library folder path with volume root and disk space (stored in DB)."""

    path: str
    volume_root: Optional[str] = None
    total: Optional[str] = None
    used: Optional[str] = None
    free: Optional[str] = None
    used_percent: Optional[float] = None
    error: Optional[str] = None


class PlexLibrarySectionDiskUsageBody(BaseModel):
    section_id: str
    section_title: str
    media_type: PlexLibraryPathMediaTypeBody
    locations: List[PlexLibraryPathDiskInfoBody]


class PlexLibraryPathsDiskUsageResponse(PlexLibraryServeMetaBody):
    """DB-backed library sections with per-path HDD stats."""

    sections: List[PlexLibrarySectionDiskUsageBody]


class PlexMediaHddDeviceBody(BaseModel):
    """One media volume (HDD/mount) with free space and library folders on it."""

    volume_root: str
    total: Optional[str] = None
    used: Optional[str] = None
    free: Optional[str] = None
    used_percent: Optional[float] = None
    error: Optional[str] = None
    library_paths: List[str] = []
    last_synced_at: Optional[datetime] = None
    disk_stats_synced_at: Optional[datetime] = None


class PlexMediaHddDevicesResponse(PlexLibraryServeMetaBody):
    devices: List[PlexMediaHddDeviceBody]
    total: int
