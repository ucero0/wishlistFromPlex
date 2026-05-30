from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


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
    """HTTP response for Deluge RPC connection test."""
    connected: bool
    status: str
    service: str = "deluge"
    error: str | None = None
    error_type: str | None = None


class DelugeRemoveRequest(BaseModel):
    """Request schema for removing a torrent from Deluge."""
    hash: str
    remove_data: bool = False

