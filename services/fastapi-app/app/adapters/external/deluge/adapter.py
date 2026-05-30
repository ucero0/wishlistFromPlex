"""Adapter for Deluge infrastructure - bridges domain and infrastructure."""
import logging
from typing import List, Optional

from app.adapters.external.deluge.mapper import to_domain_list_torrents, to_domain_torrent
from app.domain.models.external_connection import ExternalConnectionStatus
from app.domain.models.torrent import Torrent
from app.domain.ports.external.deluge.deluge_provider import DelugeProvider
from app.domain.services.connection_probe import capture_sync_connection_probe
from app.infrastructure.external_apis.deluge.client import DelugeClient
from app.infrastructure.external_apis.deluge.schemas import ExternalDelugeTorrentStatusResponse

logger = logging.getLogger(__name__)


class DelugeAdapter(DelugeProvider):
    """Adapter that converts between Deluge infrastructure and domain models."""

    def __init__(self, client: DelugeClient):
        self.client = client

    async def get_torrents(self) -> List[Torrent]:
        """Get all torrents from Deluge, mapped to domain models."""
        raw_torrents: List[ExternalDelugeTorrentStatusResponse] = (
            self.client.get_torrents_status()
        )
        return to_domain_list_torrents(raw_torrents).torrents

    async def get_torrent_status(self, hash: str) -> Torrent:
        """Get the status of a torrent from Deluge, mapped to domain model."""
        raw_torrent: ExternalDelugeTorrentStatusResponse = self.client.get_torrent_status(
            hash
        )
        return to_domain_torrent(raw_torrent)

    async def remove_torrent(self, hash: str, remove_data: bool = False) -> bool:
        """Remove a torrent from Deluge."""
        return self.client.remove_torrent(hash, remove_data)

    async def get_torrent_save_path(self, hash: str) -> Optional[str]:
        """Get the save path of a torrent from Deluge."""
        return self.client.get_torrent_save_path(hash)

    async def test_connection(self) -> ExternalConnectionStatus:
        return capture_sync_connection_probe(
            "deluge",
            self.client.probe_connection,
        )
