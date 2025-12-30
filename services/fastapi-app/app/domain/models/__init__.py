"""Domain models package - pure domain models (not ORM)."""
from app.domain.models.torrent import Torrent, TorrentStatus
from app.domain.models.media import MediaItem, MediaType
from app.domain.models.plexUser import PlexUser
from app.domain.models.torrentDownload import TorrentDownload
from app.domain.models.antivirusScan import AntivirusScan
# from app.domain.models.scanner import (
#     ScanStatusEnum,
#     ScanRequest,
#     ScanResponse,
#     ScanResultResponse,
#     ScanStatsResponse,
#     ScannerResult,
# )
# from app.domain.models.orchestration import (
#     OrchestrationRunResponse,
#     OrchestrationStatsResponse,
# )
from app.domain.models.torrent_search import (
    SearchStatusEnum,
    QualityInfo,
    TorrentSearchResult,
)

__all__ = [
    "Torrent",
    "TorrentStatus",
    "MediaItem",
    "MediaType",
    "PlexUser",
    "TorrentDownload",
    "AntivirusScan",
    # "ScanStatusEnum",
    # "ScanRequest",
    # "ScanResponse",
    # "ScanResultResponse",
    # "ScanStatsResponse",
    # "ScannerResult",
    # "OrchestrationRunResponse",
    # "OrchestrationStatsResponse",
    "SearchStatusEnum",
    "QualityInfo",
    "TorrentSearchResult",
]
