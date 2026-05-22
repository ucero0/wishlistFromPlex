"""Repository port for Plex library paths stored in the database."""
from typing import List, Protocol

from app.domain.models.plexLibraryPath import PlexLibraryPath, PlexLibraryPathMediaType


class PlexLibraryPathRepoPort(Protocol):
    async def list_active_by_media_type(
        self, media_type: PlexLibraryPathMediaType
    ) -> List[PlexLibraryPath]:
        ...

    async def list_all(self, *, active_only: bool = True) -> List[PlexLibraryPath]:
        ...

    async def sync_from_server(self, paths: List[PlexLibraryPath]) -> int:
        """
        Upsert paths from a Plex sync and deactivate rows no longer returned.

        Returns:
            Number of active paths after sync.
        """
        ...

    async def apply_disk_stats(self, paths: List[PlexLibraryPath]) -> int:
        """Persist volume and space fields on existing rows (by id). Returns rows updated."""
        ...
