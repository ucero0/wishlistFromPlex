"""
Scan a quarantined torrent for viruses and persist the scan record.

Does NOT move files, touch Deluge, or Plex.
"""
import logging
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.application.active_downloads.queries.get_active_download_queries import (
    GetActiveDownloadByUidQuery,
)
from app.domain.models.antivirus_scan import AntivirusScan
from app.domain.models.scan_result import ScanResult
from app.domain.models.active_download import ActiveDownload
from app.domain.ports.external.antivirus.antivirus_provider import AntivirusProvider
from app.domain.ports.repositories.antivirus.antivirus_repository_port import AntivirusRepoPort
from app.domain.services.filesystem_service import FilesystemService

logger = logging.getLogger(__name__)


class ScanTorrentResult(BaseModel):
    """Result of scanning a torrent in quarantine (virus check only)."""

    status: str  # "error" | "clean" | "infected"
    message: Optional[str] = None
    infected: bool = False
    scan_result: Optional[ScanResult] = None
    scan_record: Optional[AntivirusScan] = None
    scan_path: Optional[str] = None
    is_file: Optional[bool] = None
    torrent_download: Optional[ActiveDownload] = None

    class Config:
        frozen = False


class ScanTorrentUseCase:
    """Resolve torrent path, antivirus scan, persist scan record."""

    def __init__(
        self,
        get_active_download_query: GetActiveDownloadByUidQuery,
        filesystem_service: FilesystemService,
        antivirus_provider: AntivirusProvider,
        antivirus_repo: AntivirusRepoPort,
    ):
        self._get_active_download_query = get_active_download_query
        self._filesystem_service = filesystem_service
        self._antivirus_provider = antivirus_provider
        self._antivirus_repo = antivirus_repo

    async def execute(self, torrent_hash: str) -> ScanTorrentResult:
        torrent_download = await self._get_active_download_query.execute(torrent_hash)
        if not torrent_download:
            return ScanTorrentResult(
                status="error",
                message=f"Could not find torrent download with hash {torrent_hash}",
                infected=False,
            )

        scan_path = self._filesystem_service.get_quarantine_file_path(
            torrent_download.file_name
        )
        if not self._filesystem_service.path_exists(scan_path):
            return ScanTorrentResult(
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

        return ScanTorrentResult(
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
        torrent_download: ActiveDownload,
        scan_path: str,
        is_infected: bool,
        is_file: bool,
        is_dir: bool,
    ) -> AntivirusScan:
        record = AntivirusScan(
            prowlarr_guid=torrent_download.prowlarr_guid,
            file_path=scan_path if is_file else None,
            source_folder_path=scan_path if is_dir else None,
            is_infected=is_infected,
            scanned_at=datetime.now(),
        )
        return await self._antivirus_repo.create(record)
