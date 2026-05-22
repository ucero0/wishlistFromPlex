"""Adapter for Deluge infrastructure - bridges domain and infrastructure."""
import logging
from typing import List, Optional

from app.adapters.external.deluge.mapper import to_domain_list_torrents, to_domain_torrent
from app.domain.errors.deluge import DelugeError
from app.domain.models.external_connection import ExternalConnectionStatus
from app.domain.models.torrent import Torrent
from app.domain.ports.external.deluge.delugeProvider import DelugeProvider
from app.infrastructure.externalApis.deluge.client import DelugeClient
from app.infrastructure.externalApis.deluge.schemas import ExternalDelugeTorrentStatusResponse

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
        """Return structured connection status without raising."""
        try:
            connected = self.client.test_connection()
            if connected:
                return ExternalConnectionStatus(service="deluge", connected=True)
            target = self.client._connection_target()
            detail = self.client.last_connect_error
            if detail and (
                "username does not exist" in detail.lower()
                or "badlogin" in detail.lower()
            ):
                error = (
                    f"Deluge authentication failed at {target} for user "
                    f"'{self.client.username}': {detail}. "
                    f"Add the user to infra/deluge/config/auth (plain password, see infra/deluge/README.md)."
                )
            else:
                error = detail or f"Cannot connect to Deluge at {target}"
            return ExternalConnectionStatus(
                service="deluge",
                connected=False,
                error=error,
            )
        except DelugeError as exc:
            return ExternalConnectionStatus(
                service="deluge",
                connected=False,
                error=exc.message,
            )
        except Exception as exc:
            logger.exception("Unexpected error testing Deluge connection")
            return ExternalConnectionStatus(
                service="deluge",
                connected=False,
                error=str(exc),
            )
