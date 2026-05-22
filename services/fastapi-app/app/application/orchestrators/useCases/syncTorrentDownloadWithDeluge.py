"""Use case for syncing torrent download DB with Deluge status."""
import logging

from app.application.deluge.queries.getTorrentStatus import GetTorrentsStatusQuery
from app.application.torrentDownload.queries.getTorrentDownload import (
    GetAllTorrentDownloadsQuery,
)
from app.application.torrentDownload.useCases.deleteTorrentDownload import (
    DeleteTorrentDownloadUseCase,
)
from app.application.torrentDownload.useCases.updateTorrentDownload import (
    UpdateTorrentDownloadUseCase,
)
from app.domain.errors.deluge import DelugeConnectionError

logger = logging.getLogger(__name__)


class SyncTorrentDownloadWithDelugeUseCase:
    """Use case for syncing torrent download DB with Deluge status."""

    def __init__(
        self,
        getAllTorrentDownloadsQuery: GetAllTorrentDownloadsQuery,
        getTorrentsStatusQuery: GetTorrentsStatusQuery,
        deleteTorrentDownloadUseCase: DeleteTorrentDownloadUseCase,
        updateTorrentDownloadUseCase: UpdateTorrentDownloadUseCase,
    ):
        self.getAllTorrentDownloadsQuery = getAllTorrentDownloadsQuery
        self.getTorrentsStatusQuery = getTorrentsStatusQuery
        self.deleteTorrentDownloadUseCase = deleteTorrentDownloadUseCase
        self.updateTorrentDownloadUseCase = updateTorrentDownloadUseCase

    async def execute(self) -> dict:
        """
        Sync torrent download DB with Deluge status.
        For each hash in torrentDownload DB, check if it exists in Deluge.
        If not found in Deluge, remove it from torrentDownload DB.

        Returns:
            dict with sync results (removed_count, total_checked, skipped, reason)
        """
        db_torrents = await self.getAllTorrentDownloadsQuery.execute()
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
            deluge_torrents_list = await self.getTorrentsStatusQuery.execute()
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
                await self.deleteTorrentDownloadUseCase.execute(db_torrent)
                removed_count += 1
            else:
                deluge_torrent = deluge_torrents_dict[db_torrent.uid]
                updated_torrent = db_torrent.model_copy(
                    update={"file_name": deluge_torrent.file_name}
                )
                await self.updateTorrentDownloadUseCase.execute(updated_torrent)
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
