"""Deluge RPC client - infrastructure layer."""
import logging
from typing import Optional, List

from deluge_client import DelugeRPCClient

from app.core.config import settings
from app.domain.errors.deluge import (
    DelugeConnectionError,
    DelugeOperationError,
    DelugeTorrentNotFoundError,
)
from app.infrastructure.externalApis.deluge.schemas import ExternalDelugeTorrentStatusResponse

logger = logging.getLogger(__name__)


def decode_rpc(obj):
    """
    Recursively converts bytes to strings inside any structure
    (dict, list, tuple, set, etc.) returned by Deluge RPC.
    """
    if isinstance(obj, bytes):
        return obj.decode(errors="ignore")

    if isinstance(obj, dict):
        return {
            decode_rpc(key): decode_rpc(value)
            for key, value in obj.items()
        }

    if isinstance(obj, list):
        return [decode_rpc(item) for item in obj]

    if isinstance(obj, tuple):
        return tuple(decode_rpc(item) for item in obj)

    if isinstance(obj, set):
        return {decode_rpc(item) for item in obj}

    return obj


class DelugeClient:
    """Infrastructure client for Deluge RPC communication."""

    def __init__(self):
        self.host = settings.deluge_host
        self.port = settings.deluge_port
        self.username = settings.deluge_username
        self.password = settings.deluge_password
        self.client = DelugeRPCClient(
            self.host, self.port, self.username, self.password
        )
        self.is_connected = False
        self.last_connect_error: str | None = None

    def _connection_target(self) -> str:
        return f"{self.host}:{self.port}"

    def connect(self) -> bool:
        """Connect to the Deluge daemon. Prefer _ensure_connected for operational calls."""
        if self.is_connected:
            return True
        try:
            self.last_connect_error = None
            self.client.connect()
            self.is_connected = True
            return True
        except Exception as e:
            err = str(e).strip()
            self.last_connect_error = err
            if "username does not exist" in err.lower() or "badlogin" in err.lower():
                logger.error(
                    "Deluge auth failed at %s for user '%s': %s. "
                    "Add user to /config/auth (see infra/deluge/README.md).",
                    self._connection_target(),
                    self.username,
                    err,
                )
            else:
                logger.error(
                    "Error connecting to Deluge at %s: %s",
                    self._connection_target(),
                    err,
                )
            self.is_connected = False
            return False

    def _ensure_connected(self) -> None:
        if not self.connect():
            raise DelugeConnectionError(
                f"Cannot connect to Deluge at {self._connection_target()}"
            )

    def test_connection(self) -> bool:
        """Check whether Deluge RPC is reachable."""
        return self.connect()

    def disconnect(self) -> bool:
        """Disconnect from the Deluge daemon."""
        if not self.is_connected:
            return True
        try:
            self.client.disconnect()
            self.is_connected = False
            return True
        except Exception as e:
            logger.error("Error disconnecting from Deluge: %s", e)
            return False

    def get_torrents_status(self) -> List[ExternalDelugeTorrentStatusResponse]:
        """Get the status of all torrents from Deluge."""
        self._ensure_connected()
        try:
            raw_response = self.client.core.get_torrents_status(
                {}, ExternalDelugeTorrentStatusResponse.fields()
            )
            decoded_response = decode_rpc(raw_response)
            response: List[ExternalDelugeTorrentStatusResponse] = []
            for torrent_hash, torrent in decoded_response.items():
                torrent["hash"] = torrent_hash
                response.append(ExternalDelugeTorrentStatusResponse(**torrent))
            return response
        except DelugeConnectionError:
            raise
        except Exception as e:
            raise DelugeOperationError(f"Failed to list torrents from Deluge: {e}") from e

    def get_torrent_status(self, hash: str) -> ExternalDelugeTorrentStatusResponse:
        """Get the status of a torrent from Deluge."""
        self._ensure_connected()
        try:
            raw_response = self.client.core.get_torrent_status(
                hash, ExternalDelugeTorrentStatusResponse.fields()
            )
            if not raw_response:
                raise DelugeTorrentNotFoundError(hash)

            decoded_response = decode_rpc(raw_response)
            decoded_response["hash"] = hash
            return ExternalDelugeTorrentStatusResponse(**decoded_response)
        except (DelugeConnectionError, DelugeTorrentNotFoundError):
            raise
        except Exception as e:
            raise DelugeOperationError(
                f"Failed to get torrent status from Deluge (hash={hash}): {e}"
            ) from e

    def remove_torrent(self, hash: str, remove_data: bool = False) -> bool:
        """Remove a torrent from Deluge."""
        self._ensure_connected()
        try:
            raw_response = self.client.core.remove_torrent(hash, remove_data)
            return decode_rpc(raw_response)
        except DelugeConnectionError:
            raise
        except Exception as e:
            raise DelugeOperationError(
                f"Failed to remove torrent from Deluge (hash={hash}): {e}"
            ) from e

    def get_torrent_save_path(self, hash: str) -> Optional[str]:
        """Get the save path of a torrent from Deluge."""
        self._ensure_connected()
        try:
            raw_response = self.client.core.get_torrent_status(hash, ["save_path"])
            decoded_response = decode_rpc(raw_response)
            if not decoded_response:
                raise DelugeTorrentNotFoundError(hash)
            if "save_path" in decoded_response:
                return decoded_response["save_path"]
            return None
        except (DelugeConnectionError, DelugeTorrentNotFoundError):
            raise
        except Exception as e:
            raise DelugeOperationError(
                f"Failed to get save path from Deluge (hash={hash}): {e}"
            ) from e
