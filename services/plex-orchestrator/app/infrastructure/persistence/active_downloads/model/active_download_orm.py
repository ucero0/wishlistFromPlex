"""ORM model for active downloads tracked in PostgreSQL."""
from sqlalchemy import Column, DateTime, Index, Integer, String, Text
from sqlalchemy.sql import func

from app.infrastructure.persistence.base import Base


class ActiveDownloadOrm(Base):
    """Deluge download linked to Plex watchlist and Prowlarr."""

    __tablename__ = "active_downloads"

    id = Column(Integer, primary_key=True, index=True)
    guidPlex = Column(String, nullable=False, index=True)
    plexGuid = Column(String, nullable=True, index=True)
    ratingKey = Column(String, nullable=True)
    plexUserToken = Column(String, nullable=True)
    watchlistSource = Column(String, nullable=True)
    tmdbMediaId = Column(Integer, nullable=True)
    tmdbAccountId = Column(Integer, nullable=True)
    watchlistSubscribers = Column(Text, nullable=True)
    guidProwlarr = Column(String, nullable=False, index=True)
    uid = Column(String(40), unique=True, nullable=False, index=True)
    title = Column(String, nullable=False)
    fileName = Column(String, nullable=True)
    year = Column(Integer, nullable=True)
    type = Column(String, nullable=False)
    season = Column(Integer, nullable=True)
    episode = Column(Integer, nullable=True)
    episodeName = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index("idx_active_downloads_guid_plex", "guidPlex"),
        Index("idx_active_downloads_guid_prowlarr", "guidProwlarr"),
        Index("idx_active_downloads_uid", "uid"),
        Index("idx_active_downloads_type", "type"),
        Index("idx_active_downloads_plex_guid", "plexGuid"),
    )

    def __repr__(self) -> str:
        return (
            f"<ActiveDownloadOrm(title='{self.title}', "
            f"uid='{self.uid[:8]}...', type={self.type})>"
        )
