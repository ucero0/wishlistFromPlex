"""HTTP schemas for database tracking (antivirus scans, torrent downloads)."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class AntivirusScanItem(BaseModel):
    """Antivirus scan row from ``antivirus_items``."""

    id: int
    guid_prowlarr: str
    file_path: Optional[str] = None
    folder_path_src: Optional[str] = None
    folder_path_dst: Optional[str] = None
    planned_destination: Optional[str] = None
    ingest_error: Optional[str] = None
    infected: bool
    scan_datetime: datetime
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    pending_ingest: bool = Field(
        default=False,
        description="Clean scan still in quarantine (move not completed)",
    )


class AntivirusScanListResponse(BaseModel):
    items: List[AntivirusScanItem]
    total: int


class ActiveDownloadItem(BaseModel):
    """Active download row from ``active_downloads`` (Plex token omitted)."""

    id: int
    guid_plex: str
    rating_key: Optional[str] = None
    guid_prowlarr: str
    uid: str
    title: str
    file_name: Optional[str] = None
    year: Optional[int] = None
    type: str
    season: Optional[int] = None
    episode: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ActiveDownloadListResponse(BaseModel):
    items: List[ActiveDownloadItem]
    total: int


class DeferredDownloadItem(BaseModel):
    """Torrent queued until the Deluge download volume has enough free space."""

    id: int
    guid_plex: str
    rating_key: Optional[str] = None
    guid_prowlarr: str
    indexer_id: int
    torrent_title: str
    media_title: str
    year: Optional[int] = None
    media_type: str
    search_query: Optional[str] = None
    size: Optional[str] = None
    status: str
    defer_reason: Optional[str] = None
    attempt_count: int = 0
    created_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None


class DeferredDownloadListResponse(BaseModel):
    items: List[DeferredDownloadItem]
    total: int
    download_volume_path: str


class ProcessDeferredDownloadsResponse(BaseModel):
    """Result of draining the deferred queue to Deluge when space is available."""

    checked: int = 0
    sent: int = 0
    still_pending: int = 0
    failed: int = 0
