"""Probe library paths on this host and persist free space into the database."""
from datetime import datetime

from app.application.plex.services.refresh_plex_library_disk_stats import (
    refresh_disk_stats_in_database,
)
from app.domain.ports.repositories.plex.plex_library_path_repository_port import (
    PlexLibraryPathRepoPort,
)
from app.domain.services.filesystem_service import FilesystemService


class RefreshPlexLibraryDiskStatsUseCase:
    def __init__(
        self,
        path_repo: PlexLibraryPathRepoPort,
        filesystem: FilesystemService,
    ):
        self._path_repo = path_repo
        self._filesystem = filesystem

    async def execute(self, *, active_only: bool = True) -> datetime:
        return await refresh_disk_stats_in_database(
            self._path_repo,
            self._filesystem,
            active_only=active_only,
        )
