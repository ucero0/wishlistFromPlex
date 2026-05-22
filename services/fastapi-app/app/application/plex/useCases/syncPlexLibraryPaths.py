"""Persist Plex library locations from the existing locations-by-media query."""
import logging

from app.application.plex.mappers.plex_library_path_mapper import (
    locations_by_media_to_paths,
)
from app.application.plex.queries.getPlexLibraryLocations import (
    GetPlexLibraryLocationsByMediaQuery,
)
from app.application.plex.services.refreshPlexLibraryDiskStats import (
    refresh_disk_stats_in_database,
)
from app.domain.ports.repositories.plex.plexLibraryPathRepo import PlexLibraryPathRepoPort
from app.domain.services.filesystem_service import FilesystemService

logger = logging.getLogger(__name__)


class SyncPlexLibraryPathsFromServerUseCase:
    """
    Uses GetPlexLibraryLocationsByMediaQuery (same as GET /plex/servers/library/locations-by-media)
    then upserts paths into the database for ingest destination selection.
    """

    def __init__(
        self,
        locations_query: GetPlexLibraryLocationsByMediaQuery,
        path_repo: PlexLibraryPathRepoPort,
        filesystem: FilesystemService | None = None,
    ):
        self._locations_query = locations_query
        self._path_repo = path_repo
        self._filesystem = filesystem

    async def execute(self, user_token: str) -> dict:
        layout = await self._locations_query.execute(user_token)
        paths = locations_by_media_to_paths(layout)
        active_count = await self._path_repo.sync_from_server(paths)
        disk_stats_synced_at = None
        if self._filesystem is not None:
            disk_stats_synced_at = await refresh_disk_stats_in_database(
                self._path_repo, self._filesystem
            )
        logger.info(
            "Synced %s Plex library path(s) from server (%s active)",
            len(paths),
            active_count,
        )
        return {
            "sections": layout,
            "synced_from_server": len(paths),
            "active_in_database": active_count,
            "disk_stats_synced_at": disk_stats_synced_at,
        }
