"""Deluge query classes."""
from app.application.deluge.queries.get_torrent_status_query import (
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

