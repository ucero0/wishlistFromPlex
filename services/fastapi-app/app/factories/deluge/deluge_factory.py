"""Factory for Deluge query dependencies."""
from app.application.deluge.queries.get_torrent_status_query import (
    GetCompletedTorrentsQuery,
    GetDownloadingTorrentsQuery,
    GetTorrentByNameQuery,
    GetTorrentStatusQuery,
    GetTorrentsStatusQuery,
)
from app.application.deluge.queries.test_deluge_connection_query import TestDelugeConnectionQuery
from app.application.deluge.use_cases.remove_torrent_use_case import RemoveTorrentUseCase
from app.composition.deluge import (
    build_get_completed_torrents_query,
    build_get_downloading_torrents_query,
    build_get_torrent_by_name_query,
    build_get_torrent_status_query,
    build_get_torrents_status_query,
    build_remove_torrent_use_case,
    build_test_deluge_connection_query,
)


def create_test_deluge_connection_query() -> TestDelugeConnectionQuery:
    return build_test_deluge_connection_query()


def create_get_torrent_status_query() -> GetTorrentStatusQuery:
    return build_get_torrent_status_query()


def create_get_torrents_status_query() -> GetTorrentsStatusQuery:
    return build_get_torrents_status_query()


def create_get_torrent_by_name_query() -> GetTorrentByNameQuery:
    return build_get_torrent_by_name_query()


def create_get_completed_torrents_query() -> GetCompletedTorrentsQuery:
    return build_get_completed_torrents_query()


def create_get_downloading_torrents_query() -> GetDownloadingTorrentsQuery:
    return build_get_downloading_torrents_query()


def create_remove_torrent_use_case() -> RemoveTorrentUseCase:
    return build_remove_torrent_use_case()
