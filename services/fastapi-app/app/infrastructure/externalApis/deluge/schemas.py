"""External schemas for Deluge RPC API."""
from pydantic import BaseModel
from typing import List, Optional


class RpcStatusResponse(BaseModel):
    """Raw torrent status structure from Deluge RPC - external schema."""
    name: str
    state: str
    progress: float
    download_payload_rate: int
    upload_payload_rate: int
    eta: Optional[int]
    total_done: int
    total_uploaded: int
    num_peers: int
    num_seeds: int

    @classmethod
    def fields(cls) -> list[str]:
        """Return the field names that should be requested from Deluge RPC."""
        return list(cls.model_fields.keys())


class TorrentStatusResponse(BaseModel):
    """Torrent status response - external schema."""
    uid: str
    name: str
    state: str
    progress: float
    eta: Optional[int]


class ListTorrentsStatus(BaseModel):
    """List of torrent statuses - external schema."""
    torrents: List[TorrentStatusResponse]

