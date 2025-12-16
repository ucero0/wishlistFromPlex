"""Adapter for Deluge infrastructure - bridges domain and infrastructure."""
from typing import List, Optional, Dict
from app.infrastructure.externalApis.deluge.client import DelugeClient
from app.domain.models.torrent import ListTorrents
from app.adapters.external.deluge.mapper import to_domain
from app.infrastructure.externalApis.deluge.schemas import ExternalDelugeTorrentStatusResponse
from app.domain.ports.external.deluge.delugeProvider import DelugeProvider

class DelugeAdapter(DelugeProvider):
    """Adapter that converts between Deluge infrastructure and domain models."""
    
    def __init__(self, client: DelugeClient):
        self.client = client

    async def get_torrents(self) -> ListTorrents:
        """Get all torrents from Deluge, mapped to domain models."""
        raw_torrents: List[ExternalDelugeTorrentStatusResponse] = self.client.get_torrents_status()
        return to_domain(raw_torrents)

