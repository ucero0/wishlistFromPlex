"""Composition root for Deluge external integration."""
from app.adapters.external.deluge.adapter import DelugeAdapter
from app.application.deluge.queries.get_torrent_status_query import (
    GetCompletedTorrentsQuery,
    GetDownloadingTorrentsQuery,
    GetTorrentByNameQuery,
    GetTorrentStatusQuery,
    GetTorrentsStatusQuery,
)
from app.application.deluge.queries.test_deluge_connection_query import TestDelugeConnectionQuery
from app.application.deluge.use_cases.remove_torrent_use_case import RemoveTorrentUseCase
from app.infrastructure.external_apis.deluge.client import DelugeClient


def build_deluge_adapter() -> DelugeAdapter:
    return DelugeAdapter(DelugeClient())


def build_test_deluge_connection_query() -> TestDelugeConnectionQuery:
    return TestDelugeConnectionQuery(build_deluge_adapter())


def build_get_torrent_status_query() -> GetTorrentStatusQuery:
    return GetTorrentStatusQuery(build_deluge_adapter())


def build_get_torrents_status_query() -> GetTorrentsStatusQuery:
    return GetTorrentsStatusQuery(build_deluge_adapter())


def build_get_torrent_by_name_query() -> GetTorrentByNameQuery:
    return GetTorrentByNameQuery(build_deluge_adapter())


def build_get_completed_torrents_query() -> GetCompletedTorrentsQuery:
    return GetCompletedTorrentsQuery(build_get_torrents_status_query())


def build_get_downloading_torrents_query() -> GetDownloadingTorrentsQuery:
    return GetDownloadingTorrentsQuery(build_get_torrents_status_query())


def build_remove_torrent_use_case() -> RemoveTorrentUseCase:
    return RemoveTorrentUseCase(build_deluge_adapter())
