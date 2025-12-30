"""Use case for syncing torrent download DB with Deluge status."""
import logging
from app.application.torrentDownload.queries.getTorrentDownload import GetAllTorrentDownloadsQuery
from app.application.deluge.queries.getTorrentStatus import GetTorrentsStatusQuery
from app.application.torrentDownload.useCases.deleteTorrentDownload import DeleteTorrentDownloadUseCase
from app.application.torrentDownload.useCases.updateTorrentDownload import UpdateTorrentDownloadUseCase

logger = logging.getLogger(__name__)


class SyncTorrentDownloadWithDelugeUseCase:
    """Use case for syncing torrent download DB with Deluge status."""
    
    def __init__(
        self,
        getAllTorrentDownloadsQuery: GetAllTorrentDownloadsQuery,
        getTorrentsStatusQuery: GetTorrentsStatusQuery,
        deleteTorrentDownloadUseCase: DeleteTorrentDownloadUseCase,
        updateTorrentDownloadUseCase: UpdateTorrentDownloadUseCase
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
            dict with sync results (removed_count, total_checked)
        """
        # Get all torrents from DB
        db_torrents = await self.getAllTorrentDownloadsQuery.execute()
        logger.info(f"Found {len(db_torrents)} torrents in DB")
        
        if not db_torrents:
            logger.info("No torrents in DB to sync")
            return {"removed_count": 0, "total_checked": 0}
        
        # Get all torrents from Deluge
        deluge_torrents_list = await self.getTorrentsStatusQuery.execute()
        # Create a dictionary mapping hash to Deluge torrent for easy lookup
        deluge_torrents_dict = {torrent.hash: torrent for torrent in deluge_torrents_list}
        deluge_hashes = set(deluge_torrents_dict.keys())
        logger.info(f"Found {len(deluge_hashes)} torrents in Deluge")
        
        # Check each DB torrent against Deluge
        removed_count = 0
        updated_count = 0
        for db_torrent in db_torrents:
            # Check if the hash (uid) exists in Deluge
            if db_torrent.uid not in deluge_hashes:
                logger.info(f"Torrent {db_torrent.title} (hash: {db_torrent.uid[:8]}...) not found in Deluge, removing from DB")
                await self.deleteTorrentDownloadUseCase.execute(db_torrent)
                removed_count += 1
            else:
                # Always update the torrent download DB with the current status from Deluge
                # Only update fields derived from Deluge (fileName)
                deluge_torrent = deluge_torrents_dict[db_torrent.uid]
                logger.debug(f"Updating {db_torrent.title} (hash: {db_torrent.uid[:8]}...) with current Deluge fileName: '{deluge_torrent.fileName}'")
                # Copy the existing torrent and update only Deluge-derived fields
                updated_torrent = db_torrent.model_copy(update={
                    "fileName": deluge_torrent.fileName  # Update with current Deluge fileName
                })
                await self.updateTorrentDownloadUseCase.execute(updated_torrent)
                updated_count += 1
        
        logger.info(f"Sync completed: {removed_count} torrents removed, {updated_count} torrents updated out of {len(db_torrents)} checked")
        return {
            "removed_count": removed_count,
            "updated_count": updated_count,
            "total_checked": len(db_torrents)
        }

