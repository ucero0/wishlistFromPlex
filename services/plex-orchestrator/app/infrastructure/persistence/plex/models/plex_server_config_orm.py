"""ORM for Plex Media Server admin token (singleton row)."""
from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.sql import func

from app.infrastructure.persistence.base import Base

PLEX_SERVER_CONFIG_SINGLETON_ID = 1


class PlexServerConfigOrm(Base):
    __tablename__ = "plex_server_config"

    id = Column(Integer, primary_key=True, default=PLEX_SERVER_CONFIG_SINGLETON_ID)
    admin_token = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
