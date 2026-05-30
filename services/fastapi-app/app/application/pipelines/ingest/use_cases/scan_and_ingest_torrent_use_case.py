"""Scan a torrent (or reuse a clean scan), then ingest or handle infection."""
import logging

from app.application.pipelines.ingest.models.scan_and_ingest_torrent_result import (
    ScanAndIngestTorrentResult,
)
from app.application.pipelines.ingest.use_cases.handle_infected_torrent_use_case import (
    HandleInfectedTorrentUseCase,
)
from app.application.pipelines.ingest.use_cases.ingest_clean_torrent_use_case import (
    IngestCleanTorrentUseCase,
)
from app.application.pipelines.ingest.use_cases.scan_torrent_use_case import (
    ScanTorrentUseCase,
)
from app.application.active_downloads.queries.get_active_download_queries import (
    GetActiveDownloadByUidQuery,
)
from app.domain.models.antivirus_scan_status import (
    is_file_scan,
    scan_path_from_record,
)
from app.domain.ports.repositories.antivirus.antivirus_repository_port import AntivirusRepoPort
from app.domain.services.filesystem_service import FilesystemService

logger = logging.getLogger(__name__)


class ScanAndIngestTorrentUseCase:
    """Scan (or reuse a clean scan), then ingest or handle infection."""

    def __init__(
        self,
        get_active_download_query: GetActiveDownloadByUidQuery,
        scan_torrent_use_case: ScanTorrentUseCase,
        filesystem_service: FilesystemService,
        antivirus_repo: AntivirusRepoPort,
        handle_infected_torrent_use_case: HandleInfectedTorrentUseCase,
        ingest_clean_torrent_use_case: IngestCleanTorrentUseCase,
    ):
        self._get_active_download_query = get_active_download_query
        self._scan_torrent_use_case = scan_torrent_use_case
        self._filesystem_service = filesystem_service
        self._antivirus_repo = antivirus_repo
        self._handle_infected_torrent_use_case = handle_infected_torrent_use_case
        self._ingest_clean_torrent_use_case = ingest_clean_torrent_use_case

    async def execute(self, torrent_hash: str) -> ScanAndIngestTorrentResult:
        torrent_download = await self._get_active_download_query.execute(torrent_hash)
        if not torrent_download:
            return ScanAndIngestTorrentResult(
                status="error",
                message=f"Could not find torrent download with hash {torrent_hash}",
                infected=False,
                moved=False,
            )

        quarantine_root = self._filesystem_service.get_quarantine_path()
        pending = await self._antivirus_repo.get_clean_pending_ingest_by_guid_prowlarr(
            torrent_download.prowlarr_guid,
            quarantine_root,
        )
        if pending:
            record_path = scan_path_from_record(pending)
            if record_path and self._filesystem_service.path_exists(record_path):
                if pending.ingest_error:
                    logger.info(
                        "Retrying ingest for %s (previous error: %s)",
                        torrent_download.prowlarr_guid,
                        pending.ingest_error,
                    )
                return await self._ingest_clean_torrent_use_case.execute(
                    torrent_hash,
                    torrent_download,
                    pending,
                    record_path,
                    is_file_scan(pending),
                    scanned_files=[],
                    scan_skipped=True,
                )
            if record_path:
                return ScanAndIngestTorrentResult(
                    status="error",
                    message=f"Quarantine path no longer exists: {record_path}",
                    infected=False,
                    moved=False,
                    scan_skipped=True,
                )

        scan_result = await self._scan_torrent_use_case.execute(torrent_hash)

        if scan_result.status == "error":
            return ScanAndIngestTorrentResult(
                status="error",
                message=scan_result.message,
                infected=False,
                moved=False,
            )

        if scan_result.infected and scan_result.scan_result and scan_result.torrent_download:
            return await self._handle_infected_torrent_use_case.execute(
                torrent_hash, scan_result.torrent_download, scan_result.scan_result
            )

        if (
            scan_result.scan_record
            and scan_result.scan_path is not None
            and scan_result.is_file is not None
            and scan_result.torrent_download
        ):
            return await self._ingest_clean_torrent_use_case.execute(
                torrent_hash,
                scan_result.torrent_download,
                scan_result.scan_record,
                scan_result.scan_path,
                scan_result.is_file,
                scan_result.scan_result.scanned_files if scan_result.scan_result else [],
                scan_skipped=False,
            )

        return ScanAndIngestTorrentResult(
            status="error",
            message="Scan succeeded but missing data for ingest",
            infected=False,
            moved=False,
        )
