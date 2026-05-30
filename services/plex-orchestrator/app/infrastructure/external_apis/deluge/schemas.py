"""External schemas for Deluge RPC API."""
from pydantic import BaseModel
from typing import List, Optional


class ExternalDelugeTorrentStatusResponse(BaseModel):
    """Raw torrent status structure from Deluge RPC - external schema."""
    hash: str
    name: str  # Deluge RPC field name - kept as-is to match external API
    state: str
    progress: float
    download_payload_rate: int
    upload_payload_rate: int
    eta: Optional[int]
    total_done: int
    total_uploaded: int
    num_peers: int
    num_seeds: int
    save_path: Optional[str] = None
    time_added: Optional[float] = None  # Unix timestamp when torrent was added

    @classmethod
    def fields(cls) -> list[str]:
        """Return the field names that should be requested from Deluge RPC."""
        return list(cls.model_fields.keys())



