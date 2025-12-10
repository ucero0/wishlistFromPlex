"""Scanner module Pydantic schemas."""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ScanStatusEnum(str, Enum):
    """Scan status for API responses."""
    PENDING = "pending"
    SCANNING = "scanning"
    CLEAN = "clean"
    INFECTED = "infected"
    ERROR = "error"


class ScanRequest(BaseModel):
    """Request to scan a completed torrent."""
    torrent_hash: str = Field(..., min_length=40, max_length=40, description="Deluge torrent hash (40 char hex)")


class ScannerResult(BaseModel):
    """Individual scanner result."""
    scanner: str
    status: str
    details: Optional[Dict[str, Any]] = None


class ScanResponse(BaseModel):
    """Response from scan operation."""
    torrent_hash: str
    status: ScanStatusEnum
    scanners: List[ScannerResult] = []
    threat_name: Optional[str] = None
    original_path: Optional[str] = None
    destination_path: Optional[str] = None
    message: str


class ScanResultResponse(BaseModel):
    """Full scan result from database."""
    id: int
    torrent_hash: str
    status: ScanStatusEnum
    clamav_result: Optional[Dict[str, Any]] = None
    yara_result: Optional[Dict[str, Any]] = None
    original_path: Optional[str] = None
    destination_path: Optional[str] = None
    threat_name: Optional[str] = None
    scan_started_at: Optional[datetime] = None
    scan_completed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ScanStatsResponse(BaseModel):
    """Scanner statistics."""
    total_scans: int
    clean: int
    infected: int
    errors: int
    pending: int

