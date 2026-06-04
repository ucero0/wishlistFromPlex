from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.domain.models.torrent_health_config import TorrentHealthConfigUpdate


class TorrentHealthConfigResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    grace_hours: int
    min_availability: float
    unfinishable_active_minutes: int
    no_complete_copy_days: int
    stall_days: int
    skip_when_vpn_unhealthy: bool
    use_strict_when_vpn_healthy: bool
    strict_grace_hours: int
    strict_unfinishable_active_minutes: int
    strict_no_complete_copy_days: int
    strict_stall_days: int
    updated_at: datetime | None = None

    @classmethod
    def from_domain(cls, config) -> "TorrentHealthConfigResponse":
        return cls.model_validate(config.model_dump())


class UpdateTorrentHealthConfigRequest(TorrentHealthConfigUpdate):
    """Partial update; omitted fields are unchanged."""

    model_config = ConfigDict(extra="forbid")
