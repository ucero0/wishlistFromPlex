"""Domain models package - pure domain models (not ORM)."""
from app.domain.models.torrent import Torrent, TorrentStatus
from app.domain.models.media import MediaItem, MediaType
from app.domain.models.plexUser import PlexUser
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
    SearchRequest,
    SearchByQueryRequest,
    SearchResponse,
    SearchResultResponse,
    SearchStatsResponse,
    TorrentResult,
)

__all__ = [
    "Torrent",
    "TorrentStatus",
    "MediaItem",
    "MediaType",
    "PlexUser",
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
    "SearchRequest",
    "SearchByQueryRequest",
    "SearchResponse",
    "SearchResultResponse",
    "SearchStatsResponse",
    "TorrentResult",
]
