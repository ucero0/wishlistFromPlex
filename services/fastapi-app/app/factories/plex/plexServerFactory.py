from app.adapters.external.plexServer.adapter import PlexServerLibraryAdapter
from app.application.plex.queries.getPlexLibraryLocations import GetPlexLibraryLocationsByMediaQuery
from app.application.plex.queries.getPlexLibraryLocationsDiskUsage import (
    GetPlexLibraryLocationsDiskUsageQuery,
)
from app.application.plex.queries.getPlexServerItem import IsItemInLibraryQuery
from app.application.plex.queries.testPlexServerConnection import TestPlexServerConnectionQuery
from app.application.plex.useCases.partialScanLibrary import PartialScanLibraryUseCase
from app.composition.infrastructure_services import build_filesystem_service
from app.infrastructure.externalApis.plex.plexServer.client import PlexServerLibraryApiClient

def _create_plex_server_adapter() -> PlexServerLibraryAdapter:
    return PlexServerLibraryAdapter(PlexServerLibraryApiClient(token=""))


def create_test_plex_server_connection_query() -> TestPlexServerConnectionQuery:
    return TestPlexServerConnectionQuery(_create_plex_server_adapter())


def createIsItemInLibraryQuery() -> IsItemInLibraryQuery:
    """Factory function to create IsItemInLibraryQuery with its dependencies."""
    return IsItemInLibraryQuery(_create_plex_server_adapter())


def createGetPlexLibraryLocationsByMediaQuery() -> GetPlexLibraryLocationsByMediaQuery:
    """Factory for GetPlexLibraryLocationsByMediaQuery."""
    return GetPlexLibraryLocationsByMediaQuery(_create_plex_server_adapter())


def createGetPlexLibraryLocationsDiskUsageQuery() -> GetPlexLibraryLocationsDiskUsageQuery:
    """Plex library paths plus disk usage (paths must exist on this host to get stats)."""
    return GetPlexLibraryLocationsDiskUsageQuery(
        _create_plex_server_adapter(),
        build_filesystem_service(),
    )


def createPartialScanLibraryUseCase() -> PartialScanLibraryUseCase:
    """Factory function to create PartialScanLibraryUseCase with its dependencies."""
    # Token is not needed at client initialization, it's passed per request
    return PartialScanLibraryUseCase(_create_plex_server_adapter())


create_get_plex_library_locations_by_media_query = createGetPlexLibraryLocationsByMediaQuery
create_get_plex_library_locations_disk_usage_query = createGetPlexLibraryLocationsDiskUsageQuery
create_is_item_in_library_query = createIsItemInLibraryQuery
create_partial_scan_library_use_case = createPartialScanLibraryUseCase