"""Sync Plex paths (best effort) and refresh disk stats before serving from DB."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.application.plex.services.refresh_plex_library_disk_stats import (
    refresh_disk_stats_in_database,
)
from app.application.plex.use_cases.sync_plex_library_paths_use_case import (
    SyncPlexLibraryPathsFromServerUseCase,
)
from app.domain.errors.plex import PlexServerAdminTokenNotConfiguredError
from app.domain.ports.repositories.plex.plex_library_path_repository_port import PlexLibraryPathRepoPort
from app.domain.services.filesystem_service import FilesystemService

logger = logging.getLogger(__name__)


class PlexLibraryRefreshMeta(BaseModel):
    """Outcome of optional Plex sync + disk measurement."""

    plex_sync_attempted: bool = False
    plex_sync_ok: bool = False
    plex_sync_error: Optional[str] = None
    last_synced_at: Optional[datetime] = None
    disk_stats_synced_at: Optional[datetime] = None


class RefreshPlexLibraryPathsBeforeServeUseCase:
    """
    Try Plex path sync (server admin token), then refresh disk stats into ``plex_library_paths``.

    If Plex is unreachable, leaves paths unchanged and still serves last DB snapshot.
    """

    def __init__(
        self,
        path_repo: PlexLibraryPathRepoPort,
        sync_use_case: SyncPlexLibraryPathsFromServerUseCase,
        filesystem: FilesystemService,
    ):
        self._path_repo = path_repo
        self._sync = sync_use_case
        self._filesystem = filesystem

    async def execute(
        self,
        *,
        active_only: bool = True,
    ) -> PlexLibraryRefreshMeta:
        meta = PlexLibraryRefreshMeta()
        meta.plex_sync_attempted = True
        try:
            await self._sync.execute()
            meta.plex_sync_ok = True
        except PlexServerAdminTokenNotConfiguredError as exc:
            meta.plex_sync_error = exc.message
            logger.warning(
                "Plex library path sync skipped; serving last DB snapshot: %s",
                exc.message,
            )
        except Exception as exc:
            meta.plex_sync_error = str(exc)
            logger.warning(
                "Plex library path sync failed; serving last DB snapshot: %s",
                exc,
            )

        meta.disk_stats_synced_at = await refresh_disk_stats_in_database(
            self._path_repo,
            self._filesystem,
            active_only=active_only,
        )

        rows = await self._path_repo.list_all(active_only=active_only)
        if rows:
            meta.last_synced_at = max(
                (r.last_synced_at for r in rows if r.last_synced_at),
                default=None,
            )
            disk_times = [r.disk_stats_synced_at for r in rows if r.disk_stats_synced_at]
            if disk_times:
                meta.disk_stats_synced_at = max(disk_times)

        return meta
