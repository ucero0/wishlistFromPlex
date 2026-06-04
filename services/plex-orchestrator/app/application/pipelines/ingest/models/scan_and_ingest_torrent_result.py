"""Result DTO for scan-and-ingest pipeline."""
from typing import List, Optional

from pydantic import BaseModel


class ScanAndIngestTorrentResult(BaseModel):
    status: str  # "error" | "infected" | "corrupt" | "clean" | "pending_move"
    message: Optional[str] = None
    infected: bool = False
    scan_skipped: bool = False
    moved: Optional[bool] = None
    deleted: Optional[bool] = None
    destination_path: Optional[str] = None
    virus_name: Optional[str] = None
    infected_files: Optional[List[str]] = None
    corrupt_files: Optional[List[str]] = None
    yara_matches: Optional[List[str]] = None
    scanned_files: Optional[List[str]] = None
    ingest_error: Optional[str] = None
    planned_destination: Optional[str] = None

    class Config:
        frozen = False
