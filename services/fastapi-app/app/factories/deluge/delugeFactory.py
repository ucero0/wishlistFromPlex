"""Factory for Deluge query dependencies."""
from app.infrastructure.externalApis.deluge.client import DelugeClient
from app.adapters.external.deluge.adapter import DelugeAdapter
from app.application.deluge.queries.getTorrentStatus import (
    GetTorrentsStatusQuery,
    GetTorrentStatusQuery,
    GetTorrentByNameQuery,
    GetCompletedTorrentsQuery,
    GetDownloadingTorrentsQuery,
)
from app.application.deluge.useCases.removeTorrent import RemoveTorrentUseCase
from app.application.deluge.queries.testDelugeConnection import TestDelugeConnectionQuery


def _create_deluge_adapter() -> DelugeAdapter:
    return DelugeAdapter(DelugeClient())


def create_test_deluge_connection_query() -> TestDelugeConnectionQuery:
    """Factory for TestDelugeConnectionQuery."""
    return TestDelugeConnectionQuery(_create_deluge_adapter())


def createGetTorrentStatusQuery() -> GetTorrentStatusQuery:
    """Factory function to create GetTorrentStatusQuery with its dependencies."""
    return GetTorrentStatusQuery(_create_deluge_adapter())


def createGetTorrentsStatusQuery() -> GetTorrentsStatusQuery:
    """Factory function to create GetTorrentsStatusQuery with its dependencies."""
    return GetTorrentsStatusQuery(_create_deluge_adapter())

def createGetTorrentByNameQuery() -> GetTorrentByNameQuery:
    """Factory function to create GetTorrentByNameQuery with its dependencies."""
    return GetTorrentByNameQuery(_create_deluge_adapter())


def createGetCompletedTorrentsQuery() -> GetCompletedTorrentsQuery:
    """Factory function to create GetCompletedTorrentsQuery with its dependencies."""
    return GetCompletedTorrentsQuery(createGetTorrentsStatusQuery())


def createGetDownloadingTorrentsQuery() -> GetDownloadingTorrentsQuery:
    """Factory function to create GetDownloadingTorrentsQuery with its dependencies."""
    return GetDownloadingTorrentsQuery(createGetTorrentsStatusQuery())


def createRemoveTorrentUseCase() -> RemoveTorrentUseCase:
    """Factory function to create RemoveTorrentUseCase with its dependencies."""
    return RemoveTorrentUseCase(_create_deluge_adapter())
