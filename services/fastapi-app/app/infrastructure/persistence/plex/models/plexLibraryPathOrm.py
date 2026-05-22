"""ORM model for Plex library root paths."""
from sqlalchemy import BigInteger, Boolean, Column, DateTime, Float, Integer, String
from sqlalchemy.sql import func

from app.infrastructure.persistence.base import Base


class PlexLibraryPathOrm(Base):
    __tablename__ = "plex_library_paths"

    id = Column(Integer, primary_key=True, index=True)
    section_id = Column(String, nullable=False)
    section_title = Column(String, nullable=False)
    media_type = Column(String, nullable=False)
    path = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    last_synced_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    volume_root = Column(String, nullable=True)
    total_bytes = Column(BigInteger, nullable=True)
    used_bytes = Column(BigInteger, nullable=True)
    free_bytes = Column(BigInteger, nullable=True)
    used_percent = Column(Float, nullable=True)
    disk_stats_synced_at = Column(DateTime(timezone=True), nullable=True)
    disk_stats_error = Column(String, nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
