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


def create_find_best_torrent_query() -> FindBestTorrentQuery:
    """Factory function to create FindBestTorrentQuery with its dependencies."""
    client = ProwlarrClient()
    adapter = ProwlarrAdapter(client)
    quality_service = TorrentQualityService()
    return FindBestTorrentQuery(adapter, quality_service)


def create_download_torrent_use_case() -> DownloadTorrentUseCase:
    """Factory function to create DownloadTorrentUseCase with its dependencies."""
    client = ProwlarrClient()
    adapter = ProwlarrAdapter(client)
    return DownloadTorrentUseCase(adapter)


def create_test_prowlarr_connection_query() -> TestProwlarrConnectionQuery:
    """Factory function to create TestProwlarrConnectionQuery with its dependencies."""
    client = ProwlarrClient()
    adapter = ProwlarrAdapter(client)
    return TestProwlarrConnectionQuery(adapter)


def create_get_prowlarr_indexer_count_query() -> GetProwlarrIndexerCountQuery:
    """Factory function to create GetProwlarrIndexerCountQuery with its dependencies."""
    client = ProwlarrClient()
    adapter = ProwlarrAdapter(client)
    return GetProwlarrIndexerCountQuery(adapter)

