"""Deluge module Pydantic schemas."""
from pydantic import BaseModel, Field
from typing import List, ClassVar, Dict, Optional



class RpcStatusResponse(BaseModel):
    """Raw torrent status structure from Deluge RPC."""

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



class TorrentStatus(RpcStatusResponse):
    """Torrent status."""
    torrent_id: str


class listTorrentsStatus(BaseModel):
    """List of torrent statuses."""
    torrents: List[TorrentStatus]