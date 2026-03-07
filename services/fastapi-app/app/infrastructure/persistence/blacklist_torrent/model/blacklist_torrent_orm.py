"""Blacklist torrent ORM model."""
from sqlalchemy import Column, Integer, String, DateTime, Index
from sqlalchemy.sql import func

from app.infrastructure.persistence.base import Base


class BlacklistTorrentOrm(Base):
    """Torrents blacklisted by Prowlarr GUID (e.g. infected, unhealthy)."""

    __tablename__ = "blacklist_torrents"

    id = Column(Integer, primary_key=True, index=True)
    guid_prowlarr = Column(String, nullable=False, unique=True, index=True)
    reason = Column(String, nullable=False)  # e.g. "infected", "unhealthy"
    name = Column(String, nullable=True)  # Media title for display
    year = Column(Integer, nullable=True)
    type = Column(String, nullable=True)  # "movie" or "show"
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_blacklist_torrents_guid_prowlarr", "guid_prowlarr"),
    )

    def __repr__(self):
        return f"<BlacklistTorrentOrm(guid_prowlarr='{self.guid_prowlarr}', reason='{self.reason}', name='{self.name}')>"
