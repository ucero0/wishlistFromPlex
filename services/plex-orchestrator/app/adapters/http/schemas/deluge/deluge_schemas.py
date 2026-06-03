from typing import Literal, Optional

from pydantic import BaseModel, Field, ConfigDict

TorrentConnectivity = Literal["idle", "good", "stalled"]


class DelugeTorrentStatusResponse(BaseModel):
    """Response schema for Deluge torrent status."""
    model_config = ConfigDict(populate_by_name=True)

    file_name: str = Field(alias="fileName")
    hash: str
    state: str
    progress: float = 0.0
    download_speed: int = 0
    eta: Optional[int] = None
    total_size: Optional[int] = None

class DelugeConnectionResponse(BaseModel):
    """HTTP response for Deluge RPC and swarm connectivity."""
    connected: bool
    status: str
    service: str = "deluge"
    error: str | None = None
    error_type: str | None = None
    torrent_connectivity: TorrentConnectivity | None = None
    dht_nodes: int | None = None
    has_incoming_connections: bool | None = None
    downloading_count: int | None = None
    active_download_count: int | None = None
    total_download_bps: int | None = None
    total_peer_count: int | None = None


class DelugeRemoveRequest(BaseModel):
    """Request schema for removing a torrent from Deluge."""
    hash: str
    remove_data: bool = False

