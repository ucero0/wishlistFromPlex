"""Use case for scanning files with ClamAV/YARA and moving clean files."""
import logging
import os
from datetime import datetime
from typing import Optional
from app.domain.ports.external.clamav.clamavProvider import ClamAVProvider
from app.domain.services.filesystem_service import FilesystemService
from app.domain.ports.repositories.antivirus.antivirusRepo import AntivirusRepoPort
from app.domain.models.antivirusScan import AntivirusScan
from app.application.torrentDownload.queries.getTorrentDownload import GetTorrentDownloadByGuidProwlarrQuery
from app.domain.ports.external.deluge.delugeProvider import DelugeProvider

logger = logging.getLogger(__name__)


class ScanAndMoveFilesUseCase:
    """Use case for scanning files with ClamAV/YARA and moving clean files."""
    
    def __init__(
        self,
        clamav_provider: ClamAVProvider,
        filesystem_service: FilesystemService,
        antivirus_repo: AntivirusRepoPort,
        get_torrent_download_query: GetTorrentDownloadByGuidProwlarrQuery,
        deluge_provider: DelugeProvider
    ):
        self.clamav_provider = clamav_provider
        self.filesystem_service = filesystem_service
        self.antivirus_repo = antivirus_repo
        self.get_torrent_download_query = get_torrent_download_query
        self.deluge_provider = deluge_provider
    
    async def execute(self, torrent_hash: str) -> dict:
        """
        Scan files for a torrent and move clean files to media directories.
        
        Args:
            torrent_hash: The hash of the torrent to scan
            
        Returns:
            dict with scan results (status, infected, clean, moved)
        """
        # Get torrent download info to find guidProwlarr
        # We need to find the torrent download by hash (uid)
        # For now, we'll get the save path from Deluge directly
        
        # Get save path from Deluge
        save_path = await self.deluge_provider.get_torrent_save_path(torrent_hash)
        if not save_path:
            logger.error(f"Could not get save path for torrent {torrent_hash}")
            return {
                "status": "error",
                "message": "Could not get torrent save path",
                "infected": False,
                "moved": False
            }
        
        # Check if path exists
        if not os.path.exists(save_path):
            logger.error(f"Torrent save path does not exist: {save_path}")
            return {
                "status": "error",
                "message": f"Torrent save path does not exist: {save_path}",
                "infected": False,
                "moved": False
            }
        
        # Scan the file or directory using the simplified antivirus service
        scan_result = self.clamav_provider.scan(save_path)
        
        # Check if any files are infected
        is_infected = scan_result.is_infected
        is_file = os.path.isfile(save_path)
        is_dir = os.path.isdir(save_path)
        
        # Try to find the torrent download to get guidProwlarr and media type
        # We'll need to search by hash (uid) - for now, we'll use None
        guid_prowlarr = None
        media_type = "movie"  # Default
        
        # Try to find torrent download by hash (uid)
        # Note: We'd need a GetTorrentDownloadByUidQuery for this
        # For now, we'll use the hash as a fallback for guidProwlarr
        
        # Create antivirus scan record
        scan_record = AntivirusScan(
            guidProwlarr=guid_prowlarr or torrent_hash,  # Use hash as fallback
            filePath=save_path if is_file else None,
            folderPathSrc=save_path if is_dir else None,
            Infected=is_infected,
            scanDateTime=datetime.now()
        )
        
        # Save scan record
        created_scan = await self.antivirus_repo.create(scan_record)
        
        # If infected, move to quarantine
        if is_infected:
            logger.warning(f"Infected files found in {save_path}: {scan_result.infected_files}")
            # Get quarantine path from settings
            from app.core.config import settings
            quarantine_path = os.path.join(
                settings.media_quarantine_path,
                os.path.basename(save_path)
            )
            
            moved = False
            if is_file:
                moved = self.filesystem_service.move_file(save_path, quarantine_path)
            else:
                moved = self.filesystem_service.move_directory(save_path, quarantine_path)
            
            # Update scan record with quarantine path
            if moved:
                if is_file:
                    created_scan.filePath = quarantine_path
                else:
                    created_scan.folderPathDst = quarantine_path
                await self.antivirus_repo.update(created_scan)
            
            return {
                "status": "infected",
                "message": f"Found {len(scan_result.infected_files)} infected files",
                "infected": True,
                "virus_name": scan_result.virus_name,
                "infected_files": scan_result.infected_files,
                "yara_matches": scan_result.yara_matches,
                "scanned_files": scan_result.scanned_files,
                "moved": moved,
                "quarantine_path": quarantine_path if moved else None
            }
        
        # If clean, move to appropriate media directory
        # Use the media type we determined earlier (defaults to "movie")
        
        media_path = self.filesystem_service.get_media_path(media_type)
        destination_path = os.path.join(media_path, os.path.basename(save_path))
        
        moved = False
        if is_file:
            moved = self.filesystem_service.move_file(save_path, destination_path)
        else:
            moved = self.filesystem_service.move_directory(save_path, destination_path)
        
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

