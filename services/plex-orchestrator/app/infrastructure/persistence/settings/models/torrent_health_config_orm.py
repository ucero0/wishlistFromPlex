from sqlalchemy import Boolean, Column, DateTime, Float, Integer
from sqlalchemy.sql import func

from app.infrastructure.persistence.base import Base

TORRENT_HEALTH_CONFIG_SINGLETON_ID = 1


class TorrentHealthConfigOrm(Base):
    __tablename__ = "torrent_health_config"

    id = Column(Integer, primary_key=True, default=TORRENT_HEALTH_CONFIG_SINGLETON_ID)
    grace_hours = Column(Integer, nullable=False, default=6)
    min_availability = Column(Float, nullable=False, default=1.0)
    unfinishable_days = Column(Integer, nullable=False, default=1)
    no_complete_copy_days = Column(Integer, nullable=False, default=2)
    no_complete_zero_hours = Column(Integer, nullable=False, default=12)
    stall_days = Column(Integer, nullable=False, default=5)
    stall_no_peers_hours = Column(Integer, nullable=False, default=24)
    skip_when_vpn_unhealthy = Column(Boolean, nullable=False, default=True)
    use_strict_when_vpn_healthy = Column(Boolean, nullable=False, default=True)
    strict_grace_hours = Column(Integer, nullable=False, default=3)
    strict_unfinishable_days = Column(Integer, nullable=False, default=1)
    strict_no_complete_copy_days = Column(Integer, nullable=False, default=1)
    strict_no_complete_zero_hours = Column(Integer, nullable=False, default=6)
    strict_stall_days = Column(Integer, nullable=False, default=2)
    strict_stall_no_peers_hours = Column(Integer, nullable=False, default=8)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
