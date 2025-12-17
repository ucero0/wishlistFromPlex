from app.infrastructure.externalApis.plex.plexServer.client import PlexServerLibraryApiClient
from app.adapters.external.plexServer.adapter import PlexServerLibraryAdapter
from app.application.plex.queries.getPlexServerItem import IsItemInLibraryQuery
from app.core.config import settings

def createIsItemInLibraryQuery() -> IsItemInLibraryQuery:
    """Factory function to create IsItemInLibraryQuery with its dependencies."""
    client = PlexServerLibraryApiClient(settings.plex_server_url)
    adapter = PlexServerLibraryAdapter(client)
    return IsItemInLibraryQuery(adapter)