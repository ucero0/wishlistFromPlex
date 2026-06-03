"""Pydantic models for external service connection status."""
from typing import Literal

from pydantic import BaseModel, Field

TorrentConnectivity = Literal["idle", "good", "degraded", "stalled"]


class ExternalConnectionStatus(BaseModel):
    """Result of probing connectivity to an external service."""

    service: str = Field(..., description="Service identifier, e.g. deluge, prowlarr")
    connected: bool
    error: str | None = Field(
        default=None,
        description="Human-readable error when connected is False",
    )
    error_type: str | None = Field(
        default=None,
        description="Machine-readable category when connected is False, e.g. connection, server_auth",
    )
    version: str | None = Field(
        default=None,
        description="Remote service version when available (e.g. Prowlarr)",
    )
    vpn_required: bool | None = Field(
        default=None,
        description="Deluge uses Gluetun VPN path (DELUGE_HOST=gluetun)",
    )
    vpn_healthy: bool | None = Field(
        default=None,
        description="Gluetun health server reports VPN tunnel OK (independent of torrents)",
    )
    # Deluge-only swarm metrics (informational when RPC probe succeeds)
    torrent_connectivity: TorrentConnectivity | None = Field(
        default=None,
        description="idle: no active downloads; good: download traffic; degraded: peers only; stalled: no peers/traffic",
    )
    dht_nodes: int | None = None
    has_incoming_connections: bool | None = None
    downloading_count: int | None = None
    active_download_count: int | None = None
    total_download_bps: int | None = None
    total_peer_count: int | None = None

    @property
    def is_healthy(self) -> bool:
        if not self.connected:
            return False
        if self.vpn_required and self.vpn_healthy is False:
            return False
        return True
