"""Antivirus scan ORM model."""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Index
from sqlalchemy.sql import func
from app.infrastructure.persistence.base import Base


class AntivirusItem(Base):
    """Antivirus scan result item tracked by Prowlarr GUID and file paths."""
    __tablename__ = "antivirus_items"

    id = Column(Integer, primary_key=True, index=True)
    
    # Prowlarr Reference - links to Prowlarr search result
    guidProwlarr = Column(String, nullable=False, index=True)  # Prowlarr GUID
    
    # File and folder paths
    filePath = Column(String, nullable=True)  # Full path to the scanned file
    folderPathSrc = Column(String, nullable=True)  # Source folder path
    folderPathDst = Column(String, nullable=True)  # Destination folder path
    
    # Scan result
    Infected = Column(Boolean, default=False, nullable=False)  # Whether the file is infected
    
    # Scan timestamp
    scanDateTime = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_antivirus_items_guid_prowlarr", "guidProwlarr"),
        Index("idx_antivirus_items_infected", "Infected"),
        Index("idx_antivirus_items_scan_datetime", "scanDateTime"),
    )

    def __repr__(self):
        return f"<AntivirusItem(guidProwlarr='{self.guidProwlarr}', Infected={self.Infected}, filePath='{self.filePath}')>"

