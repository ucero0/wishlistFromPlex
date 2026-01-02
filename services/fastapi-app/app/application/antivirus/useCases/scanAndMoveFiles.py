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
from app.application.plex.useCases.partialScanLibrary import PartialScanLibraryUseCase
from app.core.config import settings
from pathlib import Path
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
        add_watchlist_item_use_case: AddWatchListItemUseCase,
        partial_scan_library_use_case: PartialScanLibraryUseCase
    ):
        self.antivirus_provider = antivirus_provider
        self.filesystem_service = filesystem_service
        self.antivirus_repo = antivirus_repo
        self.get_torrent_download_query = get_torrent_download_query
        self.deluge_provider = deluge_provider
        self.add_watchlist_item_use_case = add_watchlist_item_use_case
        self.partial_scan_library_use_case = partial_scan_library_use_case
    
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
        
        #if movie and a file, create a folder with the filename (without extension) and move the file inside it
        nameFolder = torrent_download.title + " (" + torrent_download.year + ")"
        if media_type == "movie" and is_file:
            destination_path = destination_path + "/" + nameFolder
        elif media_type == "tvshow" and is_file:
            destination_path = destination_path + "/" + nameFolder + "/" + torrent_download.season

        
        moved = self.filesystem_service.move(scan_path, destination_path)
        
        # Update scan record with destination path
        if moved:
            if is_file:
                created_scan.filePath = destination_path
            else:
                created_scan.folderPathDst = destination_path
            await self.antivirus_repo.update(created_scan)
            
            # Trigger partial scan of the library after moving files
            await self._trigger_partial_scan(
                torrent_download.plexUserToken,
                media_type,
                destination_path,
                is_file
            )
        
        return {
            "status": "clean",
            "message": "Files scanned and moved successfully",
            "infected": False,
            "scanned_files": scan_result.scanned_files,
            "moved": moved,
            "destination_path": destination_path if moved else None
        }
    
    async def _trigger_partial_scan(
        self,
        user_token: Optional[str],
        media_type: str,
        destination_path: str,
        is_file: bool
    ) -> None:
        """
        Trigger a partial scan of the Plex library for the moved files.
        
        Args:
            user_token: Plex user token (optional, may be None for older records)
            media_type: Type of media ("movie" or "show")
            destination_path: Path where the file/folder was moved
            is_file: Whether the moved item is a file or directory
        """
        if not user_token:
            logger.warning("Plex user token not available, skipping partial scan")
            return
        
        try:
            # Get section ID based on media type
            if media_type.lower() == "movie":
                section_id = settings.plex_movies_section_id
            elif media_type.lower() == "show" or media_type.lower() == "tvshow":
                section_id = settings.plex_tvshows_section_id
            else:
                logger.warning(f"Unknown media type: {media_type}, skipping partial scan")
                return
            
            # For files, get the parent folder (Plex scans at directory level)
            # For directories, use the directory path directly
            if is_file:
                folder_path = str(Path(destination_path).parent)
            else:
                folder_path = destination_path
            
            logger.info(f"Triggering partial scan for section {section_id}, folder: {folder_path}")
            await self.partial_scan_library_use_case.execute(
                user_token=user_token,
                section_id=section_id,
                folder_path=folder_path
            )
            logger.info(f"Successfully triggered partial scan for {media_type} at {folder_path}")
        except Exception as e:
            # Log error but don't fail the entire operation
            logger.error(f"Error triggering partial scan: {e}", exc_info=True)

