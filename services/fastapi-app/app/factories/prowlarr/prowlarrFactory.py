"""Factory for Prowlarr use cases and queries."""
from app.infrastructure.externalApis.prowlarr.prowlarr_client import ProwlarrClient
from app.adapters.external.prowlarr.adapter import ProwlarrAdapter
from app.domain.services.torrent_quality_service import TorrentQualityService
from app.application.prowlarr.useCases.downloadTorrent import DownloadTorrentUseCase
from app.application.prowlarr.queries.findBestTorrent import FindBestTorrentQuery
from app.application.prowlarr.queries.testProwlarrConnection import (
    TestProwlarrConnectionQuery,
    GetProwlarrIndexerCountQuery
)


def createFindBestTorrentQuery() -> FindBestTorrentQuery:
    """Factory function to create FindBestTorrentQuery with its dependencies."""
    client = ProwlarrClient()
    adapter = ProwlarrAdapter(client)
    quality_service = TorrentQualityService()
    return FindBestTorrentQuery(adapter, quality_service)


def createDownloadTorrentUseCase() -> DownloadTorrentUseCase:
    """Factory function to create DownloadTorrentUseCase with its dependencies."""
    client = ProwlarrClient()
    adapter = ProwlarrAdapter(client)
    return DownloadTorrentUseCase(adapter)


def createTestProwlarrConnectionQuery() -> TestProwlarrConnectionQuery:
    """Factory function to create TestProwlarrConnectionQuery with its dependencies."""
    client = ProwlarrClient()
    adapter = ProwlarrAdapter(client)
    return TestProwlarrConnectionQuery(adapter)


def createGetProwlarrIndexerCountQuery() -> GetProwlarrIndexerCountQuery:
    """Factory function to create GetProwlarrIndexerCountQuery with its dependencies."""
    client = ProwlarrClient()
    adapter = ProwlarrAdapter(client)
    return GetProwlarrIndexerCountQuery(adapter)

