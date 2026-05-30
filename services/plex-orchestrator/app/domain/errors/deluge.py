"""Domain errors for Deluge integration."""
from app.domain.errors.external import ExternalServiceError


class DelugeError(ExternalServiceError):
    """Base Deluge-related error."""

    service = "deluge"


class DelugeConnectionError(DelugeError):
    """Deluge daemon is unreachable or authentication failed."""


class DelugeOperationError(DelugeError):
    """Deluge RPC call failed after a successful connection."""


class DelugeTorrentNotFoundError(DelugeError):
    """Requested torrent hash does not exist in Deluge."""

    def __init__(self, torrent_hash: str, message: str | None = None):
        self.torrent_hash = torrent_hash
        super().__init__(
            message or f"Torrent not found in Deluge: {torrent_hash}",
        )
