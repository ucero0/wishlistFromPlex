"""Deluge module database models."""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Index, ForeignKey, Float, BigInteger, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.db import Base
import enum


class TorrentStatus(enum.Enum):
    """Torrent status enumeration."""
    QUEUED = "queued"
    DOWNLOADING = "downloading"
    SEEDING = "seeding"
    PAUSED = "paused"
    CHECKING = "checking"
    ERROR = "error"
    COMPLETED = "completed"
    REMOVED = "removed"


class TorrentItem(Base):
    """Torrent item tracked in Deluge, linked to Plex wishlist."""
    __tablename__ = "torrent_items"

    id = Column(Integer, primary_key=True, index=True)
    
    # Plex Reference - links to wishlist item
    rating_key = Column(String, nullable=False, index=True)  # Plex rating_key from WishlistItem
    
    # Torrent Identifiers
    torrent_hash = Column(String(40), unique=True, nullable=False, index=True)  # Deluge torrent hash (40 char hex)
    magnet_link = Column(String, nullable=True)  # Original magnet link used to add
    
    # Torrent Info (from Deluge daemon)
    name = Column(String, nullable=True)  # Torrent name
    status = Column(Enum(TorrentStatus), default=TorrentStatus.QUEUED, nullable=False)
    progress = Column(Float, default=0.0, nullable=False)  # 0.0 to 100.0
    
    # Size info
    total_size = Column(BigInteger, nullable=True)  # Total size in bytes
    downloaded = Column(BigInteger, default=0, nullable=False)  # Downloaded bytes
    uploaded = Column(BigInteger, default=0, nullable=False)  # Uploaded bytes
    
    # Speed info (updated on sync)
    download_speed = Column(BigInteger, default=0, nullable=False)  # bytes/sec
    upload_speed = Column(BigInteger, default=0, nullable=False)  # bytes/sec
    
    # Location
    save_path = Column(String, nullable=True)  # Download location
    
    # Peers/Seeds
    num_seeds = Column(Integer, default=0, nullable=False)
    num_peers = Column(Integer, default=0, nullable=False)
    
    # Ratio
    ratio = Column(Float, default=0.0, nullable=False)
    
    # ETA (seconds, -1 if unknown)
    eta = Column(Integer, default=-1, nullable=False)
    
    # Timestamps
    added_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_torrent_items_rating_key", "rating_key"),
        Index("idx_torrent_items_hash", "torrent_hash"),
        Index("idx_torrent_items_status", "status"),
    )

    def __repr__(self):
        return f"<TorrentItem(name='{self.name}', hash='{self.torrent_hash[:8]}...', status={self.status.value})>"

