from pydantic import BaseModel, Field, ConfigDict

class DelugeTorrentStatusResponse(BaseModel):
    """Response schema for Deluge torrent status."""
    model_config = ConfigDict(populate_by_name=True)

    file_name: str = Field(alias="fileName")
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

