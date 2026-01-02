"""Use case for scanning files with antivirus/YARA and moving clean files."""
import logging
from datetime import datetime
from typing import Optional
from app.domain.ports.external.antivirus.antivirusProvider import AntivirusProvider
from app.domain.services.filesystem_service import FilesystemService
from app.domain.ports.repositories.antivirus.antivirusRepo import AntivirusRepoPort
from app.domain.models.antivirusScan import AntivirusScan
from app.application.torrentDownload.queries.getTorrentDownload import GetTorrentDownloadByUidQuery
from app.domain.ports.external.deluge.delugeProvider import DelugeProvider
from app.application.plex.useCases.addWatchListItem import AddWatchListItemUseCase
logger = logging.getLogger(__name__)


class ScanAndMoveFilesUseCase:
    """Use case for scanning files with antivirus and moving clean files."""
    
    def __init__(
        self,
        antivirus_provider: AntivirusProvider,
        filesystem_service: FilesystemService,
        antivirus_repo: AntivirusRepoPort,
        get_torrent_download_query: GetTorrentDownloadByUidQuery,
        deluge_provider: DelugeProvider,
        add_watchlist_item_use_case: AddWatchListItemUseCase
    ):
        self.antivirus_provider = antivirus_provider
        self.filesystem_service = filesystem_service
        self.antivirus_repo = antivirus_repo
        self.get_torrent_download_query = get_torrent_download_query
        self.deluge_provider = deluge_provider
        self.add_watchlist_item_use_case = add_watchlist_item_use_case
    
    async def execute(self, torrent_hash: str) -> dict:
        """
        Scan files for a torrent and move clean files to media directories.
        
        Args:
            torrent_hash: The hash (uid) of the torrent to scan
            
        Returns:
            dict with scan results (status, infected, clean, moved)
        """
        # Get torrent download by hash (uid)
        torrent_download = await self.get_torrent_download_query.execute(torrent_hash)
        if not torrent_download:
            logger.error(f"Could not find torrent download with hash {torrent_hash}")
            return {
                "status": "error",
                "message": f"Could not find torrent download with hash {torrent_hash}",
                "infected": False,
                "moved": False
            }
        

        fileName = torrent_download.fileName
        media_type = torrent_download.type
        
        # Build scan path: containerQuarantinepath/name
        scan_path = self.filesystem_service.get_quarantine_file_path(fileName)
        
        # Check if path exists
        if not self.filesystem_service.path_exists(scan_path):
            logger.error(f"Scan path does not exist: {scan_path}")
            return {
                "status": "error",
                "message": f"Scan path does not exist: {scan_path}",
                "infected": False,
                "moved": False
            }
        
        # Remove all files that aren't video files or subtitles before scanning
        removed_count = self.filesystem_service.remove_non_media_files(scan_path)
        if removed_count > 0:
            logger.info(f"Removed {removed_count} non-media file(s) before scanning")

        # Scan the file or directory using the antivirus service
        scan_result = self.antivirus_provider.scan(scan_path)
        
        # Check if any files are infected
        is_infected = scan_result.is_infected
        is_file = self.filesystem_service.is_file(scan_path)
        is_dir = self.filesystem_service.is_directory(scan_path)
        
        # Create antivirus scan record
        scan_record = AntivirusScan(
            guidProwlarr=torrent_download.guidProwlarr,
            filePath=scan_path if is_file else None,
            folderPathSrc=scan_path if is_dir else None,
            Infected=is_infected,
            scanDateTime=datetime.now()
        )
        
        # Save scan record
        created_scan = await self.antivirus_repo.create(scan_record)
        
        # If infected, remove the torrent and its files using Deluge
        if is_infected:
            logger.warning(f"Infected files found in {scan_path}: {scan_result.infected_files}")
            
            deleted = await self.deluge_provider.remove_torrent(torrent_hash, remove_data=True)
            
            # Add to watchlist again for re-download
            try:
                if not torrent_download.ratingKey:
                    logger.warning(
                        f"RatingKey not available for item {torrent_download.title} (guidPlex: {torrent_download.guidPlex}). "
                        f"Cannot add back to watchlist. This may happen for older records created before ratingKey was stored."
                    )
                elif not torrent_download.plexUserToken:
                    logger.warning(
                        f"Plex user token not available for item {torrent_download.title} (guidPlex: {torrent_download.guidPlex}). "
                        f"Cannot add back to watchlist. This may happen for older records created before plexUserToken was stored."
                    )
                else:
                    # Add item back to watchlist using the stored ratingKey and plexUserToken
                    await self.add_watchlist_item_use_case.execute(torrent_download.ratingKey, torrent_download.plexUserToken)
                    logger.info(f"Added item {torrent_download.title} back to watchlist for re-download")
            except Exception as e:
                logger.error(f"Error adding item back to watchlist: {e}", exc_info=True)
            
            return {
                "status": "infected",
                "message": f"Found {len(scan_result.infected_files)} infected files",
                "infected": True,
                "virus_name": scan_result.virus_name,
                "infected_files": scan_result.infected_files,
                "yara_matches": scan_result.yara_matches,
                "scanned_files": scan_result.scanned_files,
                "deleted": deleted
            }
        
        # If clean, move to appropriate media directory based on type
        # If type is movie: move to containerPlexPath/movies
        # If type is tvshow: move to containerPlexPath/tvshow
        destination_path = self.filesystem_service.get_media_destination_path(media_type, fileName)
        
        moved = self.filesystem_service.move(scan_path, destination_path)
        
        # Update scan record with destination path
        if moved:
            if is_file:
                created_scan.filePath = destination_path
            else:
                created_scan.folderPathDst = destination_path
            await self.antivirus_repo.update(created_scan)
        
        return {
            "status": "clean",
            "message": "Files scanned and moved successfully",
            "infected": False,
            "scanned_files": scan_result.scanned_files,
            "moved": moved,
            "destination_path": destination_path if moved else None
        }

