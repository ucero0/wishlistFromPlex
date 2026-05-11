"""Query: list Plex library section root paths for movies and TV shows."""
from app.domain.models.plexLibraryLocations import PlexLibraryLocationsByMedia
from app.domain.ports.external.plex.plexServerLibraryProvider import PlexServerLibraryProvider


class GetPlexLibraryLocationsByMediaQuery:
    """Application service for resolving library folder layout from Plex Server."""

    def __init__(self, provider: PlexServerLibraryProvider):
        self._provider = provider

    async def execute(self, user_token: str) -> PlexLibraryLocationsByMedia:
        return await self._provider.get_library_locations_by_media(user_token)
