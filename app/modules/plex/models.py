"""Plex module database models."""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Index, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.db import Base
import enum


class MediaType(enum.Enum):
    """Media type enumeration."""
    MOVIE = "movie"
    SHOW = "show"
    SEASON = "season"
    EPISODE = "episode"


class PlexUser(Base):
    """Plex user with authentication token."""
    __tablename__ = "plex_users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    plex_token = Column(String, nullable=False)
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationship to wishlist_item_sources
    wishlist_sources = relationship("WishlistItemSource", back_populates="plex_user", cascade="all, delete-orphan")


class WishlistItem(Base):
    """Item on the Plex watchlist."""
    __tablename__ = "wishlist_items"

    id = Column(Integer, primary_key=True, index=True)
    
    # Plex Identifiers
    guid = Column(String, unique=True, nullable=False, index=True)  # Plex GUID - used for account-level operations
    rating_key = Column(String, nullable=True, index=True)  # Local server ratingKey - used for server-level operations
    
    # Media Info
    title = Column(String, nullable=False, index=True)
    year = Column(Integer, nullable=True, index=True)
    media_type = Column(Enum(MediaType), nullable=True)
    
    # Additional Metadata
    summary = Column(Text, nullable=True)
    thumb = Column(String, nullable=True)
    art = Column(String, nullable=True)
    content_rating = Column(String, nullable=True)
    studio = Column(String, nullable=True)
    
    # Timestamps
    added_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_seen_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationship to wishlist_item_sources
    sources = relationship("WishlistItemSource", back_populates="wishlist_item", cascade="all, delete-orphan")

    __table_args__ = (Index("idx_wishlist_items_guid", "guid"),)


class WishlistItemSource(Base):
    """Tracks which users have which wishlist items."""
    __tablename__ = "wishlist_item_sources"

    id = Column(Integer, primary_key=True, index=True)
    wishlist_item_id = Column(Integer, ForeignKey("wishlist_items.id", ondelete="CASCADE"), nullable=False, index=True)
    plex_user_id = Column(Integer, ForeignKey("plex_users.id", ondelete="CASCADE"), nullable=False, index=True)
    first_added_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_seen_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    wishlist_item = relationship("WishlistItem", back_populates="sources")
    plex_user = relationship("PlexUser", back_populates="wishlist_sources")

    __table_args__ = (
        Index("idx_wishlist_item_sources_item_user", "wishlist_item_id", "plex_user_id"),
    )

