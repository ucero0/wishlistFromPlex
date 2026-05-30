"""Deluge external API package."""
from app.infrastructure.external_apis.deluge.client import DelugeClient
from app.infrastructure.external_apis.deluge.schemas import ExternalDelugeTorrentStatusResponse

__all__ = [
    "DelugeClient",
    "ExternalDelugeTorrentStatusResponse",
]
