"""Factory for Prowlarr use cases and queries."""
from app.infrastructure.externalApis.prowlarr.prowlarr_client import ProwlarrClient
from app.adapters.external.prowlarr.adapter import ProwlarrAdapter
from app.domain.services.torrent_quality_service import TorrentQualityService
from app.application.prowlarr.useCases.searchTorrentsByQuery import SearchTorrentsByQueryUseCase
from app.application.prowlarr.queries.testProwlarrConnection import (
    TestProwlarrConnectionQuery,
    GetProwlarrIndexerCountQuery
)


def create_search_torrents_by_query_use_case() -> SearchTorrentsByQueryUseCase:
    """Factory function to create SearchTorrentsByQueryUseCase with its dependencies."""
    client = ProwlarrClient()
    adapter = ProwlarrAdapter(client)
    quality_service = TorrentQualityService()
    return SearchTorrentsByQueryUseCase(adapter, quality_service)


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

