"""Refresh DB library paths from Plex for active users (scheduled / background)."""
import logging

from app.application.plex.useCases.syncPlexLibraryPaths import (
    SyncPlexLibraryPathsFromServerUseCase,
)
from app.domain.ports.repositories.plex.plexUserRepo import PlexUserRepoPort

logger = logging.getLogger(__name__)


class SyncPlexLibraryPathsForActiveUsersUseCase:
    """
    Syncs library paths using the first active Plex user token.

    One Plex server returns the same library layout for all local users; a single
    sync is enough to update the DB when folders are added or removed.
    """

    def __init__(
        self,
        user_repo: PlexUserRepoPort,
        sync_use_case: SyncPlexLibraryPathsFromServerUseCase,
    ):
        self._user_repo = user_repo
        self._sync = sync_use_case

    async def execute(self) -> dict:
        users = await self._user_repo.get_active_users()
        if not users:
            logger.warning(
                "No active Plex users in DB; cannot sync library paths from server"
            )
            return {
                "users_synced": 0,
                "synced_from_server": 0,
                "active_in_database": 0,
                "errors": [],
            }

        user = users[0]
        if len(users) > 1:
            logger.debug(
                "Syncing Plex library paths once using user %s (%d active users)",
                user.name,
                len(users),
            )

        try:
            last_result = await self._sync.execute(user.plex_token)
            logger.info(
                "Synced Plex library paths (%s paths, %s active in DB)",
                last_result["synced_from_server"],
                last_result["active_in_database"],
            )
            return {
                "users_synced": 1,
                "synced_from_server": last_result["synced_from_server"],
                "active_in_database": last_result["active_in_database"],
                "errors": [],
            }
        except Exception as exc:
            msg = f"{user.name}: {exc}"
            logger.error("Plex library path sync failed: %s", exc)
            return {
                "users_synced": 0,
                "synced_from_server": 0,
                "active_in_database": 0,
                "errors": [msg],
            }
