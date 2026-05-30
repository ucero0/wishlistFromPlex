"""Torrent download query classes."""
from app.application.active_downloads.queries.get_active_download_queries import (
    GetActiveDownloadByIdQuery,
    GetActiveDownloadByUidQuery,
    GetActiveDownloadsByGuidPlexQuery,
    IsGuidPlexDownloadingQuery,
    GetActiveDownloadByGuidProwlarrQuery,
    GetActiveDownloadsByTypeQuery,
    GetAllActiveDownloadsQuery,
)

__all__ = [
    "GetActiveDownloadByIdQuery",
    "GetActiveDownloadByUidQuery",
    "GetActiveDownloadsByGuidPlexQuery",
    "IsGuidPlexDownloadingQuery",
    "GetActiveDownloadByGuidProwlarrQuery",
    "GetActiveDownloadsByTypeQuery",
    "GetAllActiveDownloadsQuery",
]

