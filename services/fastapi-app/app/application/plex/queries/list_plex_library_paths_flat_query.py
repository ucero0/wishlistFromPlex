"""Query: list Plex library path rows from the database (flat, not grouped by section)."""
from typing import List

from app.domain.models.plex_library_path import PlexLibraryPath
from app.domain.ports.repositories.plex.plex_library_path_repository_port import PlexLibraryPathRepoPort


class ListPlexLibraryPathsFlatQuery:
    def __init__(self, path_repo: PlexLibraryPathRepoPort):
        self._path_repo = path_repo

    async def execute(self, *, active_only: bool = True) -> List[PlexLibraryPath]:
        return await self._path_repo.list_all(active_only=active_only)
