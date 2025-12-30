"""Adapter for Deluge infrastructure - bridges domain and infrastructure."""
from typing import List, Optional, Dict
from app.infrastructure.externalApis.deluge.client import DelugeClient
from app.domain.models.torrent import ListTorrents, Torrent
from app.adapters.external.deluge.mapper import to_domain_torrent, to_domain_list_torrents
from app.infrastructure.externalApis.deluge.schemas import ExternalDelugeTorrentStatusResponse
from app.domain.ports.external.deluge.delugeProvider import DelugeProvider

class DelugeAdapter(DelugeProvider):
    """Adapter that converts between Deluge infrastructure and domain models."""
    
    def __init__(self, client: DelugeClient):
        self.client = client

    async def get_torrents(self) -> ListTorrents:
        """Get all torrents from Deluge, mapped to domain models."""
        raw_torrents: List[ExternalDelugeTorrentStatusResponse] = self.client.get_torrents_status()
        return to_domain_list_torrents(raw_torrents)

    async def get_torrent_status(self, hash: str) -> Torrent:
        """Get the status of a torrent from Deluge, mapped to domain model."""
        raw_torrent: ExternalDelugeTorrentStatusResponse = self.client.get_torrent_status(hash)
        return to_domain_torrent(raw_torrent)

    async def remove_torrent(self, hash: str, remove_data: bool = False) -> bool:
        """Remove a torrent from Deluge."""
        return self.client.remove_torrent(hash, remove_data)
    
    async def get_torrent_save_path(self, hash: str) -> Optional[str]:
        """Get the save path of a torrent from Deluge."""
        return self.client.get_torrent_save_path(hash)