"""Factory for Deluge query dependencies."""
from app.infrastructure.externalApis.deluge.client import DelugeClient
from app.adapters.external.deluge.adapter import DelugeAdapter
from app.application.deluge.queries.getTorrentStatus import GetTorrentsStatusQuery, GetTorrentStatusQuery
from app.application.deluge.useCases.removeTorrent import RemoveTorrentUseCase

def createGetTorrentStatusQuery() -> GetTorrentStatusQuery:
    """Factory function to create GetTorrentStatusQuery with its dependencies."""
    client = DelugeClient()
    adapter = DelugeAdapter(client)
    return GetTorrentStatusQuery(adapter)


def createGetTorrentsStatusQuery() -> GetTorrentsStatusQuery:
    """Factory function to create GetTorrentsStatusQuery with its dependencies."""
    client = DelugeClient()
    adapter = DelugeAdapter(client)
    return GetTorrentsStatusQuery(adapter)

def createRemoveTorrentUseCase() -> RemoveTorrentUseCase:
    """Factory function to create RemoveTorrentUseCase with its dependencies."""
    client = DelugeClient()
    adapter = DelugeAdapter(client)
    return RemoveTorrentUseCase(adapter)
