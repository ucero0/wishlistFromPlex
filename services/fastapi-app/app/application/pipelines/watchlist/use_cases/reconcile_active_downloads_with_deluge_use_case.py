"""Reconcile tracked download records with Deluge state."""
import logging

from app.application.deluge.queries.get_torrent_status_query import GetTorrentsStatusQuery
from app.application.active_downloads.queries.get_active_download_queries import (
    GetAllActiveDownloadsQuery,
)
from app.application.active_downloads.use_cases.delete_active_download_use_case import (
    DeleteActiveDownloadUseCase,
)
from app.application.active_downloads.use_cases.update_active_download_use_case import (
    UpdateActiveDownloadUseCase,
)
from app.domain.errors.deluge import DelugeConnectionError

logger = logging.getLogger(__name__)


class ReconcileActiveDownloadsWithDelugeUseCase:
    """Align DB download rows with Deluge (remove stale, update file names)."""

    def __init__(
        self,
        get_all_active_downloads_query: GetAllActiveDownloadsQuery,
        get_torrents_status_query: GetTorrentsStatusQuery,
        delete_active_download_use_case: DeleteActiveDownloadUseCase,
        update_active_download_use_case: UpdateActiveDownloadUseCase,
    ):
        self._get_all_active_downloads_query = get_all_active_downloads_query
        self._get_torrents_status_query = get_torrents_status_query
        self._delete_active_download_use_case = delete_active_download_use_case
        self._update_active_download_use_case = update_active_download_use_case

    async def execute(self) -> dict:
        db_torrents = await self._get_all_active_downloads_query.execute()
        logger.info("Found %s torrents in DB", len(db_torrents))

        if not db_torrents:
            logger.info("No torrents in DB to sync")
            return {
                "removed_count": 0,
                "updated_count": 0,
                "total_checked": 0,
                "skipped": False,
            }

        try:
            deluge_torrents_list = await self._get_torrents_status_query.execute()
        except DelugeConnectionError as exc:
            logger.warning(
                "Skipping torrent download DB sync: Deluge is not reachable (%s)",
                exc.message,
            )
            return {
                "removed_count": 0,
                "updated_count": 0,
                "total_checked": len(db_torrents),
                "skipped": True,
                "reason": "deluge_unavailable",
            }

        if not deluge_torrents_list:
            logger.warning(
                "Deluge returned no torrents while DB has entries; "
                "skipping destructive sync to avoid accidental DB cleanup"
            )
            return {
                "removed_count": 0,
                "updated_count": 0,
                "total_checked": len(db_torrents),
                "skipped": True,
                "reason": "deluge_empty_response",
            }

        deluge_torrents_dict = {torrent.hash: torrent for torrent in deluge_torrents_list}
        deluge_hashes = set(deluge_torrents_dict.keys())
        logger.info("Found %s torrents in Deluge", len(deluge_hashes))

        removed_count = 0
        updated_count = 0
        for db_torrent in db_torrents:
            if db_torrent.uid not in deluge_hashes:
                logger.info(
                    "Torrent %s (hash: %s...) not found in Deluge, removing from DB",
                    db_torrent.title,
                    db_torrent.uid[:8],
                )
                await self._delete_active_download_use_case.execute(db_torrent)
                removed_count += 1
            else:
                deluge_torrent = deluge_torrents_dict[db_torrent.uid]
                updated_torrent = db_torrent.model_copy(
                    update={"file_name": deluge_torrent.file_name}
                )
                await self._update_active_download_use_case.execute(updated_torrent)
                updated_count += 1

        logger.info(
            "Sync completed: %s removed, %s updated out of %s checked",
            removed_count,
            updated_count,
            len(db_torrents),
        )
        return {
            "removed_count": removed_count,
            "updated_count": updated_count,
            "total_checked": len(db_torrents),
            "skipped": False,
        }
