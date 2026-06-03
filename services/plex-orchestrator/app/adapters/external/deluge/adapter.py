"""Adapter for Deluge infrastructure - bridges domain and infrastructure."""
import logging
from typing import List, Optional

from app.adapters.external.deluge.mapper import to_domain_list_torrents, to_domain_torrent
from app.domain.models.external_connection import ExternalConnectionStatus
from app.domain.models.torrent import Torrent
from app.domain.ports.external.deluge.deluge_provider import DelugeProvider
from app.domain.services.connection_probe import capture_sync_connection_probe
from app.domain.services.deluge_path_health import probe_deluge_path_health
from app.domain.services.deluge_swarm_health import classify_torrent_connectivity
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
        status = capture_sync_connection_probe(
            "deluge",
            self.client.probe_connection,
        )
        if not status.connected:
            return status

        path_health = probe_deluge_path_health()
        status = status.model_copy(
            update={
                "vpn_required": path_health.vpn_required,
                "vpn_healthy": path_health.vpn_healthy,
            }
        )
        if path_health.vpn_required and not path_health.vpn_healthy:
            return status.model_copy(
                update={
                    "error": path_health.error,
                    "error_type": "connection",
                }
            )

        return self._with_swarm_metrics(status)

    def _with_swarm_metrics(self, status: ExternalConnectionStatus) -> ExternalConnectionStatus:
        """Attach per-torrent swarm stats for visibility only (not VPN health)."""
        try:
            session = self.client.get_session_status(
                ["dht_nodes", "has_incoming_connections"]
            )
            torrents = self.client.get_torrents_status()
        except Exception as exc:
            logger.warning("Deluge RPC ok but swarm stats failed: %s", exc)
            return status

        metrics = classify_torrent_connectivity(
            [t.model_dump() for t in torrents],
            dht_nodes=session.get("dht_nodes"),
            has_incoming_connections=session.get("has_incoming_connections"),
        )
        return status.model_copy(update=metrics)
