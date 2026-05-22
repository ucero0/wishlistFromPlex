"""Sync Plex paths (best effort) and refresh disk stats before serving from DB."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.application.plex.services.refreshPlexLibraryDiskStats import (
    refresh_disk_stats_in_database,
)
from app.application.plex.useCases.syncPlexLibraryPaths import (
    SyncPlexLibraryPathsFromServerUseCase,
)
from app.domain.ports.repositories.plex.plexLibraryPathRepo import PlexLibraryPathRepoPort
from app.domain.ports.repositories.plex.plexUserRepo import PlexUserRepoPort
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
    Try Plex path sync, then refresh disk stats into ``plex_library_paths``.

    If Plex is unreachable, leaves paths unchanged and still serves last DB snapshot.
    """

    def __init__(
        self,
        path_repo: PlexLibraryPathRepoPort,
        user_repo: PlexUserRepoPort,
        sync_use_case: SyncPlexLibraryPathsFromServerUseCase,
        filesystem: FilesystemService,
    ):
        self._path_repo = path_repo
        self._user_repo = user_repo
        self._sync = sync_use_case
        self._filesystem = filesystem

    async def execute(
        self,
        *,
        user_token: str | None = None,
        active_only: bool = True,
    ) -> PlexLibraryRefreshMeta:
        meta = PlexLibraryRefreshMeta()
        token = user_token
        if not token:
            users = await self._user_repo.get_active_users()
            if users:
                token = users[0].plex_token

        if token:
            meta.plex_sync_attempted = True
            try:
                await self._sync.execute(token)
                meta.plex_sync_ok = True
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
