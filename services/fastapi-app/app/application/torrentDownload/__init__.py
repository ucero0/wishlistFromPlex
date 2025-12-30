"""Torrent download application layer."""
from app.application.torrentDownload.queries import (
    GetTorrentDownloadByIdQuery,
    GetTorrentDownloadByUidQuery,
    GetTorrentDownloadsByGuidPlexQuery,
    IsGuidPlexDownloadingQuery,
    GetTorrentDownloadByGuidProwlarrQuery,
    GetTorrentDownloadsByTypeQuery,
    GetAllTorrentDownloadsQuery,
)
from app.application.torrentDownload.useCases import (
    CreateTorrentDownloadUseCase,
    UpdateTorrentDownloadUseCase,
    DeleteTorrentDownloadUseCase,
    DeleteTorrentDownloadByIdUseCase,
)

__all__ = [
    "GetTorrentDownloadByIdQuery",
    "GetTorrentDownloadByUidQuery",
    "GetTorrentDownloadsByGuidPlexQuery",
    "IsGuidPlexDownloadingQuery",
    "GetTorrentDownloadByGuidProwlarrQuery",
    "GetTorrentDownloadsByTypeQuery",
    "GetAllTorrentDownloadsQuery",
    "CreateTorrentDownloadUseCase",
    "UpdateTorrentDownloadUseCase",
    "DeleteTorrentDownloadUseCase",
    "DeleteTorrentDownloadByIdUseCase",
]

