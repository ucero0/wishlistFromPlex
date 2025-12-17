"""Factory for Plex watchlist adapter."""
from app.infrastructure.externalApis.plex.plexClient.client import PlexWatchlistClient
from app.adapters.external.plexClient.adapter import PlexWatchlistAdapter
from app.application.plex.queries.getWatchList import GetWatchListQuery
from app.application.plex.useCases.removeWatchListItem import RemoveWatchListItemUseCase

def createGetWatchListQuery() -> GetWatchListQuery:
    """Factory function to create GetWatchListQuery with its dependencies."""
    client = PlexWatchlistClient()
    adapter = PlexWatchlistAdapter(client)
    return GetWatchListQuery(adapter)


def createRemoveWatchListItemUseCase() -> RemoveWatchListItemUseCase:
    """Factory function to create RemoveWatchListItemUseCase with its dependencies."""
    client = PlexWatchlistClient()
    adapter = PlexWatchlistAdapter(client)
    return RemoveWatchListItemUseCase(adapter)