"""Torrent ORM models."""
from sqlalchemy import Column, Integer, String, DateTime, Index
from sqlalchemy.sql import func
from app.infrastructure.persistence.base import Base


class TorrentItem(Base):
    """Torrent download item linked to Plex wishlist and Prowlarr."""
    __tablename__ = "torrent_items"

    id = Column(Integer, primary_key=True, index=True)
    
    # Plex Reference - links to wishlist item
    guidPlex = Column(String, nullable=False, index=True)  # Plex GUID
    ratingKey = Column(String, nullable=True)  # Plex ratingKey for adding back to watchlist
    plexUserToken = Column(String, nullable=True)  # Plex user token for adding back to watchlist
    
    # Prowlarr Reference - links to Prowlarr search result
    guidProwlarr = Column(String, nullable=False, index=True)  # Prowlarr GUID
    
    # Torrent Identifier
    uid = Column(String(40), unique=True, nullable=False, index=True)  # Torrent UID (40 char hex)
    
    # Media Information
    title = Column(String, nullable=False)  # Media title
    fileName = Column(String, nullable=True)  # File name from Deluge
    year = Column(Integer, nullable=True)  # Release year
    type = Column(String, nullable=False)  # Media type: "movie" or "show"
    
    # TV Show specific fields (optional)
    season = Column(Integer, nullable=True)  # Season number (for TV shows)
    episode = Column(Integer, nullable=True)  # Episode number (for TV shows)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_torrent_items_guid_plex", "guidPlex"),
        Index("idx_torrent_items_guid_prowlarr", "guidProwlarr"),
        Index("idx_torrent_items_uid", "uid"),
        Index("idx_torrent_items_type", "type"),
    )

    def __repr__(self):
        return f"<TorrentItem(title='{self.title}', uid='{self.uid[:8]}...', type={self.type})>"

