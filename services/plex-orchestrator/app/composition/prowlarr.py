"""Composition root for Prowlarr external integration."""
from app.adapters.external.prowlarr.adapter import ProwlarrAdapter
from app.application.prowlarr.queries.find_best_torrent_query import GetBestTorrentsQuery
from app.application.prowlarr.queries.test_prowlarr_connection_query import (
    GetProwlarrIndexerCountQuery,
    TestProwlarrConnectionQuery,
)
from app.application.prowlarr.use_cases.download_torrent_use_case import DownloadTorrentUseCase
from app.domain.services.torrent_quality_service import TorrentQualityService
from app.infrastructure.external_apis.prowlarr.prowlarr_client import ProwlarrClient


def build_prowlarr_adapter() -> ProwlarrAdapter:
    return ProwlarrAdapter(ProwlarrClient())


def build_find_best_torrent_query() -> GetBestTorrentsQuery:
    return GetBestTorrentsQuery(build_prowlarr_adapter(), TorrentQualityService())


def build_download_torrent_use_case() -> DownloadTorrentUseCase:
    return DownloadTorrentUseCase(build_prowlarr_adapter())


def build_test_prowlarr_connection_query() -> TestProwlarrConnectionQuery:
    return TestProwlarrConnectionQuery(build_prowlarr_adapter())


def build_get_prowlarr_indexer_count_query() -> GetProwlarrIndexerCountQuery:
    return GetProwlarrIndexerCountQuery(build_prowlarr_adapter())
