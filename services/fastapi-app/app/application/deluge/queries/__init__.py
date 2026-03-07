"""Deluge query classes."""
from app.application.deluge.queries.getTorrentStatus import (
    GetTorrentsStatusQuery,
    GetTorrentStatusQuery,
    GetCompletedTorrentsQuery,
    GetDownloadingTorrentsQuery,
)

__all__ = [
    "GetTorrentsStatusQuery",
    "GetTorrentStatusQuery",
    "GetCompletedTorrentsQuery",
    "GetDownloadingTorrentsQuery",
]

