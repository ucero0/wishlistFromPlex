"""Scanner module database models."""
from sqlalchemy import Column, Integer, String, DateTime, Index, ForeignKey, Text, Enum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.db import Base
import enum


class ScanStatus(enum.Enum):
    """Scan result status enumeration."""
    PENDING = "pending"
    SCANNING = "scanning"
    CLEAN = "clean"
    INFECTED = "infected"
    ERROR = "error"


class ScanResult(Base):
    """Virus scan result for a torrent/file."""
    __tablename__ = "scan_results"

    id = Column(Integer, primary_key=True, index=True)
    
    # Link to torrent
    torrent_hash = Column(String(40), nullable=False, index=True)
    
    # Scan info
    status = Column(Enum(ScanStatus), default=ScanStatus.PENDING, nullable=False)
    
    # Scanner results (JSON for flexibility)
    clamav_result = Column(JSON, nullable=True)  # {"status": "clean/infected", "virus_name": "..."}
    yara_result = Column(JSON, nullable=True)    # {"status": "clean/infected", "matched_rules": [...]}
    
    # File paths
    original_path = Column(String, nullable=True)
    destination_path = Column(String, nullable=True)
    
    # Threat info (aggregated)
    threat_name = Column(String, nullable=True)  # Combined threat name if infected
    
    # Timestamps
    scan_started_at = Column(DateTime(timezone=True), nullable=True)
    scan_completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_scan_results_torrent_hash", "torrent_hash"),
        Index("idx_scan_results_status", "status"),
    )

    def __repr__(self):
        return f"<ScanResult(torrent_hash='{self.torrent_hash[:8]}...', status={self.status.value})>"

