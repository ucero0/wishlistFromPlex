"""Torrent unhealthy-removal policy in PostgreSQL. Defaults below; change via PUT /deluge/torrent-health."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TorrentHealthConfig(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = 1
    grace_hours: int = 6
    min_availability: float = 1.0
    unfinishable_days: int = 1
    no_complete_copy_days: int = 2
    no_complete_zero_hours: int = 12
    stall_days: int = 5
    stall_no_peers_hours: int = 24
    skip_when_vpn_unhealthy: bool = True
    use_strict_when_vpn_healthy: bool = True
    strict_grace_hours: int = 3
    strict_unfinishable_days: int = 1
    strict_no_complete_copy_days: int = 1
    strict_no_complete_zero_hours: int = 6
    strict_stall_days: int = 2
    strict_stall_no_peers_hours: int = 8
    updated_at: datetime | None = None


class TorrentHealthConfigUpdate(BaseModel):
    grace_hours: int | None = Field(default=None, ge=0, le=168)
    min_availability: float | None = Field(default=None, ge=0, le=10)
    unfinishable_days: int | None = Field(default=None, ge=0, le=90)
    no_complete_copy_days: int | None = Field(default=None, ge=0, le=90)
    no_complete_zero_hours: int | None = Field(default=None, ge=1, le=168)
    stall_days: int | None = Field(default=None, ge=1, le=90)
    stall_no_peers_hours: int | None = Field(default=None, ge=1, le=168)
    skip_when_vpn_unhealthy: bool | None = None
    use_strict_when_vpn_healthy: bool | None = None
    strict_grace_hours: int | None = Field(default=None, ge=0, le=168)
    strict_unfinishable_days: int | None = Field(default=None, ge=0, le=90)
    strict_no_complete_copy_days: int | None = Field(default=None, ge=0, le=90)
    strict_no_complete_zero_hours: int | None = Field(default=None, ge=1, le=168)
    strict_stall_days: int | None = Field(default=None, ge=1, le=90)
    strict_stall_no_peers_hours: int | None = Field(default=None, ge=1, le=168)
