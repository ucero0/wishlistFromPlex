"""Query: Plex library locations loaded from the database (same shape as server query)."""
from app.application.plex.mappers.plex_library_path_mapper import (
    paths_to_locations_by_media,
)
from app.domain.models.plexLibraryLocations import PlexLibraryLocationsByMedia
from app.domain.ports.repositories.plex.plexLibraryPathRepo import PlexLibraryPathRepoPort


class ListPlexLibraryPathsFromDbQuery:
    """Returns PlexLibraryLocationsByMedia built from persisted paths."""

    def __init__(self, path_repo: PlexLibraryPathRepoPort):
        self._path_repo = path_repo

    async def execute(self, *, active_only: bool = True) -> PlexLibraryLocationsByMedia:
        rows = await self._path_repo.list_all(active_only=active_only)
        return paths_to_locations_by_media(rows)
