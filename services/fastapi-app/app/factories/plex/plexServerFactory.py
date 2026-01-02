from app.infrastructure.externalApis.plex.plexServer.client import PlexServerLibraryApiClient
from app.adapters.external.plexServer.adapter import PlexServerLibraryAdapter
from app.application.plex.queries.getPlexServerItem import IsItemInLibraryQuery
from app.application.plex.useCases.partialScanLibrary import PartialScanLibraryUseCase
from app.core.config import settings

def createIsItemInLibraryQuery() -> IsItemInLibraryQuery:
    """Factory function to create IsItemInLibraryQuery with its dependencies."""
    # Token is not needed at client initialization, it's passed per request
    client = PlexServerLibraryApiClient(token="")
    adapter = PlexServerLibraryAdapter(client)
    return IsItemInLibraryQuery(adapter)

def createPartialScanLibraryUseCase() -> PartialScanLibraryUseCase:
    """Factory function to create PartialScanLibraryUseCase with its dependencies."""
    # Token is not needed at client initialization, it's passed per request
    client = PlexServerLibraryApiClient(token="")
    adapter = PlexServerLibraryAdapter(client)
    return PartialScanLibraryUseCase(adapter)