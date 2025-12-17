"""Factory for Deluge query dependencies."""
from app.infrastructure.externalApis.deluge.client import DelugeClient
from app.adapters.external.deluge.adapter import DelugeAdapter
from app.application.deluge.queries.getTorrentStatus import GetTorrentStatusQuery

def createGetTorrentStatusQuery() -> GetTorrentStatusQuery:
    """Factory function to create GetTorrentStatusQuery with its dependencies."""
    client = DelugeClient()
    adapter = DelugeAdapter(client)
    return GetTorrentStatusQuery(adapter)

