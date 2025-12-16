"""Factory for Plex watchlist adapter."""
from app.infrastructure.externalApis.plex.plexClient.client import PlexWatchlistClient
from app.adapters.external.plexClient.adapter import PlexWatchlistAdapter
from app.application.plex.queries.getWatchList import GetWatchListQuery

def getPlexWatchlistAdapter() -> GetWatchListQuery:
    client = PlexWatchlistClient()
    adapter = PlexWatchlistAdapter(client)
    return GetWatchListQuery(adapter)


