from app.adapters.external.plexServer.adapter import PlexServerLibraryAdapter
from app.application.plex.queries.getPlexLibraryLocations import GetPlexLibraryLocationsByMediaQuery
from app.application.plex.queries.getPlexLibraryLocationsDiskUsage import (
    GetPlexLibraryLocationsDiskUsageQuery,
)
from app.application.plex.queries.getPlexServerItem import IsItemInLibraryQuery
from app.application.plex.useCases.partialScanLibrary import PartialScanLibraryUseCase
from app.core.config import settings
from app.infrastructure.externalApis.plex.plexServer.client import PlexServerLibraryApiClient
from app.infrastructure.services.filesystem_service_impl import FilesystemServiceImpl

def createIsItemInLibraryQuery() -> IsItemInLibraryQuery:
    """Factory function to create IsItemInLibraryQuery with its dependencies."""
    # Token is not needed at client initialization, it's passed per request
    client = PlexServerLibraryApiClient(token="")
    adapter = PlexServerLibraryAdapter(client)
    return IsItemInLibraryQuery(adapter)


def createGetPlexLibraryLocationsByMediaQuery() -> GetPlexLibraryLocationsByMediaQuery:
    """Factory for GetPlexLibraryLocationsByMediaQuery."""
    client = PlexServerLibraryApiClient(token="")
    adapter = PlexServerLibraryAdapter(client)
    return GetPlexLibraryLocationsByMediaQuery(adapter)


def createGetPlexLibraryLocationsDiskUsageQuery() -> GetPlexLibraryLocationsDiskUsageQuery:
    """Plex library paths plus disk usage (paths must exist on this host to get stats)."""
    client = PlexServerLibraryApiClient(token="")
    adapter = PlexServerLibraryAdapter(client)
    filesystem = FilesystemServiceImpl(
        plex_media_path=settings.container_plex_media_path,
        quarantine_path=settings.container_deluge_quarantine_path,
    )
    return GetPlexLibraryLocationsDiskUsageQuery(adapter, filesystem)


def createPartialScanLibraryUseCase() -> PartialScanLibraryUseCase:
    """Factory function to create PartialScanLibraryUseCase with its dependencies."""
    # Token is not needed at client initialization, it's passed per request
    client = PlexServerLibraryApiClient(token="")
    adapter = PlexServerLibraryAdapter(client)
    return PartialScanLibraryUseCase(adapter)