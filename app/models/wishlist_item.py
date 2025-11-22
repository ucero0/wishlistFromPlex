from sqlalchemy import Column, Integer, String, DateTime, Index, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.db import Base


class WishlistItem(Base):
    __tablename__ = "wishlist_items"

    id = Column(Integer, primary_key=True, index=True)
    uid = Column(String, unique=True, nullable=False, index=True)  # Plex GUID
    title = Column(String, nullable=False, index=True)
    year = Column(Integer, nullable=True, index=True)
    added_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_seen_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationship to wishlist_item_sources
    sources = relationship("WishlistItemSource", back_populates="wishlist_item", cascade="all, delete-orphan")

    # Index on uid for fast lookups
    __table_args__ = (Index("idx_wishlist_items_uid", "uid"),)


class WishlistItemSource(Base):
    __tablename__ = "wishlist_item_sources"

    id = Column(Integer, primary_key=True, index=True)
    wishlist_item_id = Column(Integer, ForeignKey("wishlist_items.id", ondelete="CASCADE"), nullable=False, index=True)
    plex_user_id = Column(Integer, ForeignKey("plex_users.id", ondelete="CASCADE"), nullable=False, index=True)
    first_added_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_seen_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    wishlist_item = relationship("WishlistItem", back_populates="sources")
    plex_user = relationship("PlexUser", back_populates="wishlist_sources")

    # Unique constraint on item+user combination
    __table_args__ = (
        Index("idx_wishlist_item_sources_item_user", "wishlist_item_id", "plex_user_id"),
    )

