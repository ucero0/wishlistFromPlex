"""Adapter for Deluge infrastructure - bridges domain and infrastructure."""
from typing import List, Optional
from sqlalchemy.orm import Session

from app.infrastructure.deluge.client import DelugeClient
from app.infrastructure.deluge.schemas import RpcStatusResponse
from app.infrastructure.deluge.mapper import map_rpc_response_to_domain
from app.domain.models.torrent import Torrent


class DelugeAdapter:
    """Adapter that converts between Deluge infrastructure and domain models."""
    
    def __init__(self, client: DelugeClient):
        self.client = client
    
    async def get_torrents(self, guid_plex: Optional[str] = None) -> List[Torrent]:
        """Get all torrents from Deluge, mapped to domain models."""
        raw_torrents = self.client.get_torrents_status(RpcStatusResponse.fields())
        
        domain_torrents = []
        for torrent_id, rpc_data in raw_torrents.items():
            # If guid_plex is provided, filter by it
            # Otherwise, we'd need to look it up from the database
            domain_torrent = map_rpc_response_to_domain(
                torrent_id=torrent_id,
                rpc_data=rpc_data,
                guid_plex=guid_plex or ""  # Would need to fetch from DB
            )
            domain_torrents.append(domain_torrent)
        
        return domain_torrents

