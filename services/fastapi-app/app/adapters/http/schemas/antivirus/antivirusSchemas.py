"""Schemas for antivirus API requests and responses."""
from typing import Optional, List
from pydantic import BaseModel


# Request Schemas
class ScanPathRequest(BaseModel):
    """Request model for scanning a file or directory path."""
    path: str


class ScanTorrentRequest(BaseModel):
    """Request model for scanning a torrent."""
    torrent_hash: str


# Response Schemas
class ScanSummary(BaseModel):
    """Summary of scan results."""
    total_scanned: int
    total_infected: int


class ScanPathResponse(BaseModel):
    """Response model for scanning a file or directory path."""
    status: str  # "clean" or "infected"
    infected: bool
    virus_name: Optional[str] = None
    yara_matches: List[str] = []
    scanned_files: List[str] = []
    infected_files: List[str] = []
    summary: ScanSummary


class HealthCheckResponse(BaseModel):
    """Response model for antivirus health check."""
    service: str
    connected: bool
    status: str  # "healthy" or "unhealthy"
    error: Optional[str] = None


class ScanTorrentResponse(BaseModel):
    """Response model for scan-only (no move/ingest). No moved, deleted, or destination_path."""
    status: str  # "clean", "infected", or "error"
    message: Optional[str] = None
    infected: bool
    virus_name: Optional[str] = None
    infected_files: Optional[List[str]] = None
    yara_matches: Optional[List[str]] = None
    scanned_files: Optional[List[str]] = None


class ScanTorrentAndIngestResponse(BaseModel):
    """Response model for scan + ingest: includes move/delete outcome and destination_path."""
    status: str  # "clean", "infected", "error", or "pending_move"
    message: Optional[str] = None
    infected: bool
    scan_skipped: bool = False
    virus_name: Optional[str] = None
    infected_files: Optional[List[str]] = None
    yara_matches: Optional[List[str]] = None
    scanned_files: Optional[List[str]] = None
    moved: Optional[bool] = None
    deleted: Optional[bool] = None
    destination_path: Optional[str] = None
    ingest_error: Optional[str] = None
    planned_destination: Optional[str] = None

