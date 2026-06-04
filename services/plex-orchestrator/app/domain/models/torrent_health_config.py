"""Torrent unhealthy-removal policy in PostgreSQL. Defaults below; change via PUT /deluge/torrent-health."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TorrentHealthConfig(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = 1
    grace_hours: int = 6
    min_availability: float = 1.0
    unfinishable_active_minutes: int = 20
    no_complete_copy_days: int = 2
    stall_days: int = 5
    skip_when_vpn_unhealthy: bool = True
    use_strict_when_vpn_healthy: bool = True
    strict_grace_hours: int = 3
    strict_unfinishable_active_minutes: int = 20
    strict_no_complete_copy_days: int = 1
    strict_stall_days: int = 2
    updated_at: datetime | None = None


class TorrentHealthConfigUpdate(BaseModel):
    grace_hours: int | None = Field(default=None, ge=0, le=168)
    min_availability: float | None = Field(default=None, ge=0, le=10)
    unfinishable_active_minutes: int | None = Field(default=None, ge=1, le=1440)
    no_complete_copy_days: int | None = Field(default=None, ge=0, le=90)
    stall_days: int | None = Field(default=None, ge=1, le=90)
    skip_when_vpn_unhealthy: bool | None = None
    use_strict_when_vpn_healthy: bool | None = None
    strict_grace_hours: int | None = Field(default=None, ge=0, le=168)
    strict_unfinishable_active_minutes: int | None = Field(
        default=None, ge=1, le=1440
    )
    strict_no_complete_copy_days: int | None = Field(default=None, ge=0, le=90)
    strict_stall_days: int | None = Field(default=None, ge=1, le=90)
