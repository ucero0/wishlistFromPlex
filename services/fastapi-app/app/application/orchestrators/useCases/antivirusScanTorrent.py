"""
Orchestrator: antivirus scan of a torrent's files only.

Coordinates torrent download lookup, filesystem path, antivirus scan, and scan record persistence.
Does NOT move files, touch Deluge, or Plex. Named to differentiate from other possible scan types.
"""
import logging
from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from app.application.torrentDownload.queries.getTorrentDownload import (
    GetTorrentDownloadByUidQuery,
)
from app.domain.models.antivirusScan import AntivirusScan
from app.domain.models.scanResult import ScanResult
from app.domain.models.torrentDownload import TorrentDownload
from app.domain.ports.external.antivirus.antivirusProvider import AntivirusProvider
from app.domain.ports.repositories.antivirus.antivirusRepo import AntivirusRepoPort
from app.domain.services.filesystem_service import FilesystemService

logger = logging.getLogger(__name__)


class AntivirusScanTorrentResult(BaseModel):
    """
    Result of antivirus-scanning a torrent (virus check only).
    Includes scan outcome and, on success, the created record and path info for downstream use.
    """

    status: str  # "error" | "clean" | "infected"
    message: Optional[str] = None
    infected: bool = False
    scan_result: Optional[ScanResult] = None
    scan_record: Optional[AntivirusScan] = None
    scan_path: Optional[str] = None
    is_file: Optional[bool] = None
    torrent_download: Optional[TorrentDownload] = None

    class Config:
        frozen = False


class AntivirusScanTorrentUseCase:
    """Orchestrates: resolve torrent path, antivirus scan, persist scan record. No move, no Deluge, no Plex."""

    def __init__(
        self,
        get_torrent_download_query: GetTorrentDownloadByUidQuery,
        filesystem_service: FilesystemService,
        antivirus_provider: AntivirusProvider,
        antivirus_repo: AntivirusRepoPort,
    ):
        self._get_torrent_download_query = get_torrent_download_query
        self._filesystem_service = filesystem_service
        self._antivirus_provider = antivirus_provider
        self._antivirus_repo = antivirus_repo

    async def execute(self, torrent_hash: str) -> AntivirusScanTorrentResult:
        """Resolve torrent path, scan for viruses, persist record. Returns result with status and scan details."""
        torrent_download = await self._get_torrent_download_query.execute(torrent_hash)
        if not torrent_download:
            return AntivirusScanTorrentResult(
                status="error",
                message=f"Could not find torrent download with hash {torrent_hash}",
                infected=False,
            )

        scan_path = self._filesystem_service.get_quarantine_file_path(
            torrent_download.fileName
        )
        if not self._filesystem_service.path_exists(scan_path):
            return AntivirusScanTorrentResult(
                status="error",
                message=f"Scan path does not exist: {scan_path}",
                infected=False,
            )

        self._remove_non_media_files_from(scan_path)
        scan_result = self._antivirus_provider.scan(scan_path)
        is_file = self._filesystem_service.is_file(scan_path)
        is_dir = self._filesystem_service.is_directory(scan_path)

        scan_record = await self._persist_scan_record(
            torrent_download, scan_path, scan_result.is_infected, is_file, is_dir
        )

        return AntivirusScanTorrentResult(
            status="infected" if scan_result.is_infected else "clean",
            message=None,
            infected=scan_result.is_infected,
            scan_result=scan_result,
            scan_record=scan_record,
            scan_path=scan_path,
            is_file=is_file,
            torrent_download=torrent_download,
        )

    def _remove_non_media_files_from(self, scan_path: str) -> None:
        removed_count = self._filesystem_service.remove_non_media_files(scan_path)
        if removed_count > 0:
            logger.info(f"Removed {removed_count} non-media file(s) before scanning")

    async def _persist_scan_record(
        self,
        torrent_download: TorrentDownload,
        scan_path: str,
        is_infected: bool,
        is_file: bool,
        is_dir: bool,
    ) -> AntivirusScan:
        record = AntivirusScan(
            guidProwlarr=torrent_download.guidProwlarr,
            filePath=scan_path if is_file else None,
            folderPathSrc=scan_path if is_dir else None,
            Infected=is_infected,
            scanDateTime=datetime.now(),
        )
        return await self._antivirus_repo.create(record)
