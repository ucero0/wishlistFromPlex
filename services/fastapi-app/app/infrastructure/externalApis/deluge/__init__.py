"""Deluge external API package."""
from app.infrastructure.externalApis.deluge.client import DelugeClient
from app.infrastructure.externalApis.deluge.schemas import ExternalDelugeTorrentStatusResponse

__all__ = [
    "DelugeClient",
    "ExternalDelugeTorrentStatusResponse",
]
