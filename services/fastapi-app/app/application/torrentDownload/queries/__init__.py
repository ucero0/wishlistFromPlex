"""Torrent download query classes."""
from app.application.torrentDownload.queries.getTorrentDownload import (
    GetTorrentDownloadByIdQuery,
    GetTorrentDownloadByUidQuery,
    GetTorrentDownloadsByGuidPlexQuery,
    IsGuidPlexDownloadingQuery,
    GetTorrentDownloadByGuidProwlarrQuery,
    GetTorrentDownloadsByTypeQuery,
    GetAllTorrentDownloadsQuery,
)

__all__ = [
    "GetTorrentDownloadByIdQuery",
    "GetTorrentDownloadByUidQuery",
    "GetTorrentDownloadsByGuidPlexQuery",
    "IsGuidPlexDownloadingQuery",
    "GetTorrentDownloadByGuidProwlarrQuery",
    "GetTorrentDownloadsByTypeQuery",
    "GetAllTorrentDownloadsQuery",
]

