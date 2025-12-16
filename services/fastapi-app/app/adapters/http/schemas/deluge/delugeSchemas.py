from pydantic import BaseModel

class DelugeTorrentStatusResponse(BaseModel):
    """Response schema for Deluge torrent status."""
    name: str
    state: str
    progress: float
    download_speed: int
    eta: int
    total_size: int


