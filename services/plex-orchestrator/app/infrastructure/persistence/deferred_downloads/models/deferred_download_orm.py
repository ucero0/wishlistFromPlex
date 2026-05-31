"""ORM for torrents deferred until download volume has space."""
from sqlalchemy import BigInteger, Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from app.infrastructure.persistence.base import Base


class DeferredDownloadOrm(Base):
    __tablename__ = "deferred_downloads"

    id = Column(Integer, primary_key=True, index=True)
    guid_plex = Column(String, nullable=False, index=True)
    plex_guid = Column(String, nullable=True, index=True)
    rating_key = Column(String, nullable=True)
    plex_user_token = Column(String, nullable=True)
    watchlist_source = Column(String, nullable=True)
    tmdb_media_id = Column(Integer, nullable=True)
    tmdb_account_id = Column(Integer, nullable=True)
    watchlistSubscribers = Column(Text, nullable=True)
    guid_prowlarr = Column(String, nullable=False)
    indexer_id = Column(Integer, nullable=False)
    torrent_title = Column(String, nullable=False)
    media_title = Column(String, nullable=False)
    year = Column(Integer, nullable=True)
    media_type = Column(String, nullable=False)
    season = Column(Integer, nullable=True)
    episode = Column(Integer, nullable=True)
    episodeName = Column(String, nullable=True)
    search_query = Column(String, nullable=True)
    size_bytes = Column(BigInteger, nullable=True)
    magnet_url = Column(String, nullable=True)
    status = Column(String, nullable=False, default="pending")
    defer_reason = Column(String, nullable=True)
    attempt_count = Column(Integer, nullable=False, default=0)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    sent_at = Column(DateTime(timezone=True), nullable=True)
