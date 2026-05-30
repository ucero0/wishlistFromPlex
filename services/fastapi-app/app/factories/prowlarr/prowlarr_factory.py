"""Factory for Prowlarr use cases and queries."""
from app.application.prowlarr.queries.find_best_torrent_query import GetBestTorrentsQuery
from app.application.prowlarr.queries.test_prowlarr_connection_query import (
    GetProwlarrIndexerCountQuery,
    TestProwlarrConnectionQuery,
)
from app.application.prowlarr.use_cases.download_torrent_use_case import DownloadTorrentUseCase
from app.composition.prowlarr import (
    build_download_torrent_use_case,
    build_find_best_torrent_query,
    build_get_prowlarr_indexer_count_query,
    build_test_prowlarr_connection_query,
)


def create_find_best_torrent_query() -> GetBestTorrentsQuery:
    return build_find_best_torrent_query()


def create_download_torrent_use_case() -> DownloadTorrentUseCase:
    return build_download_torrent_use_case()


def create_test_prowlarr_connection_query() -> TestProwlarrConnectionQuery:
    return build_test_prowlarr_connection_query()


def create_get_prowlarr_indexer_count_query() -> GetProwlarrIndexerCountQuery:
    return build_get_prowlarr_indexer_count_query()
