"""Query: list Plex library section root paths (movie, tvshow, other) from Plex Server API."""
from app.domain.models.plex_library_locations import PlexLibraryLocationsByMedia
from app.domain.ports.external.plex.plex_server_library_provider import PlexServerLibraryProvider


class GetPlexLibraryLocationsByMediaQuery:
    """Application service for resolving library folder layout from Plex Server."""

    def __init__(self, provider: PlexServerLibraryProvider):
        self._provider = provider

    async def execute(self) -> PlexLibraryLocationsByMedia:
        return await self._provider.get_library_locations_by_media()
