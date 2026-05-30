"""Refresh DB library paths from Plex using the server admin token (scheduled / background)."""
import logging

from app.application.plex.use_cases.sync_plex_library_paths_use_case import (
    SyncPlexLibraryPathsFromServerUseCase,
)
from app.domain.errors.plex import PlexServerAdminTokenNotConfiguredError

logger = logging.getLogger(__name__)


class SyncPlexLibraryPathsForActiveUsersUseCase:
    """
    Syncs library paths from the local Plex Media Server.

    Uses PLEX_SERVER_ADMIN_TOKEN (server operator), not per-user watchlist tokens.
    """

    def __init__(
        self,
        sync_use_case: SyncPlexLibraryPathsFromServerUseCase,
    ):
        self._sync = sync_use_case

    async def execute(self) -> dict:
        try:
            last_result = await self._sync.execute()
            logger.info(
                "Synced Plex library paths (%s paths, %s active in DB)",
                last_result["synced_from_server"],
                last_result["active_in_database"],
            )
            return {
                "users_synced": 0,
                "synced_from_server": last_result["synced_from_server"],
                "active_in_database": last_result["active_in_database"],
                "errors": [],
            }
        except PlexServerAdminTokenNotConfiguredError as exc:
            logger.warning("Plex library path sync skipped: %s", exc.message)
            return {
                "users_synced": 0,
                "synced_from_server": 0,
                "active_in_database": 0,
                "errors": [exc.message],
            }
        except Exception as exc:
            msg = str(exc)
            logger.error("Plex library path sync failed: %s", exc)
            return {
                "users_synced": 0,
                "synced_from_server": 0,
                "active_in_database": 0,
                "errors": [msg],
            }
