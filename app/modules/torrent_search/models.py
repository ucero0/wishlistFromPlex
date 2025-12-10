"""Torrent search module database models."""
from sqlalchemy import Column, Integer, String, DateTime, Index, ForeignKey, Float, Boolean, Enum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.db import Base
import enum


class SearchStatus(enum.Enum):
    """Search status enumeration."""
    PENDING = "pending"
    SEARCHING = "searching"
    FOUND = "found"
    NOT_FOUND = "not_found"
    ADDED = "added"
    ERROR = "error"


class TorrentSearchResult(Base):
    """Torrent search result for a wishlist item."""
    __tablename__ = "torrent_search_results"

    id = Column(Integer, primary_key=True, index=True)
    
    # Link to wishlist item
    rating_key = Column(String, nullable=False, index=True)
    
    # Search info
    status = Column(Enum(SearchStatus), default=SearchStatus.PENDING, nullable=False)
    search_query = Column(String, nullable=True)
    
    # Selected torrent info
    selected_torrent_title = Column(String, nullable=True)
    selected_torrent_indexer = Column(String, nullable=True)
    selected_torrent_size = Column(Float, nullable=True)  # Size in bytes
    selected_torrent_seeders = Column(Integer, nullable=True)
    selected_torrent_quality_score = Column(Integer, nullable=True)
    
    # Quality details (JSON for flexibility)
    quality_info = Column(JSON, nullable=True)  # {"resolution": "2160p", "audio": "TrueHD", ...}
    
    # All search results (JSON array for reference)
    all_results = Column(JSON, nullable=True)
    
    # Link to torrent if added
    torrent_hash = Column(String(40), nullable=True, index=True)
    
    # Timestamps
    searched_at = Column(DateTime(timezone=True), nullable=True)
    added_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_torrent_search_rating_key", "rating_key"),
        Index("idx_torrent_search_status", "status"),
    )

    def __repr__(self):
        return f"<TorrentSearchResult(rating_key='{self.rating_key}', status={self.status.value})>"



