from pydantic import BaseModel

class DelugeTorrentStatusResponse(BaseModel):
    """Response schema for Deluge torrent status."""
    fileName: str
    hash: str
    state: str
    progress: float
    download_speed: int
    eta: int
    total_size: int

class DelugeRemoveRequest(BaseModel):
    """Request schema for removing a torrent from Deluge."""
    hash: str
    remove_data: bool = False

