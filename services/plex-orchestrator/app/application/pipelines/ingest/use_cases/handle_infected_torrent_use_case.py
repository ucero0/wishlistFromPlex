"""Handle infected torrent: blacklist, remove from Deluge, retry with a new torrent."""
import logging

from app.application.blacklist_torrent.use_cases import AddTorrentToBlacklistUseCase
from app.application.pipelines.ingest.models.retry_active_download_outcome import (
    RetryActiveDownloadOutcome,
)
from app.application.pipelines.ingest.models.scan_and_ingest_torrent_result import (
    ScanAndIngestTorrentResult,
)
from app.application.pipelines.ingest.use_cases.retry_active_download_use_case import (
    RetryActiveDownloadUseCase,
)
from app.application.pipelines.watchlist.use_cases.reconcile_active_downloads_with_deluge_use_case import (
    ReconcileActiveDownloadsWithDelugeUseCase,
)
from app.domain.models.scan_result import ScanResult
from app.domain.models.active_download import ActiveDownload
from app.domain.ports.external.deluge.deluge_provider import DelugeProvider

logger = logging.getLogger(__name__)


class HandleInfectedTorrentUseCase:
    def __init__(
        self,
        deluge_provider: DelugeProvider,
        add_torrent_to_blacklist_use_case: AddTorrentToBlacklistUseCase,
        retry_active_download_use_case: RetryActiveDownloadUseCase,
        reconcile_active_downloads_use_case: ReconcileActiveDownloadsWithDelugeUseCase,
    ):
        self._deluge_provider = deluge_provider
        self._add_torrent_to_blacklist_use_case = add_torrent_to_blacklist_use_case
        self._retry_active_download = retry_active_download_use_case
        self._reconcile_active_downloads_use_case = reconcile_active_downloads_use_case

    async def execute(
        self,
        torrent_hash: str,
        torrent_download: ActiveDownload,
        scan_result: ScanResult,
    ) -> ScanAndIngestTorrentResult:
        logger.warning("Infected files found: %s", scan_result.infected_files)
        await self._add_torrent_to_blacklist_use_case.execute(
            torrent_download.prowlarr_guid,
            reason="infected",
            name=torrent_download.title,
            year=torrent_download.year,
            media_type=torrent_download.type,
        )
        deleted = await self._deluge_provider.remove_torrent(
            torrent_hash, remove_data=True
        )
        outcome = await self._retry_active_download.execute(
            torrent_download, blacklist_reason="infected"
        )
        if outcome == RetryActiveDownloadOutcome.SUCCESS:
            logger.info(
                "Queued replacement torrent for infected download '%s'",
                torrent_download.title,
            )
        elif outcome == RetryActiveDownloadOutcome.DEFERRED:
            logger.info(
                "Deferred replacement torrent for infected download '%s'",
                torrent_download.title,
            )
        else:
            logger.warning(
                "No replacement torrent queued for infected download '%s' (%s)",
                torrent_download.title,
                outcome.value,
            )
        await self._reconcile_active_downloads()
        return ScanAndIngestTorrentResult(
            status="infected",
            message=f"Found {len(scan_result.infected_files)} infected files",
            infected=True,
            virus_name=scan_result.virus_name,
            infected_files=scan_result.infected_files,
            yara_matches=scan_result.yara_matches,
            scanned_files=scan_result.scanned_files,
            deleted=deleted,
        )

    async def _reconcile_active_downloads(self) -> None:
        try:
            result = await self._reconcile_active_downloads_use_case.execute()
            if result.get("skipped"):
                logger.warning(
                    "Active download reconcile skipped after infected handling: reason=%s",
                    result.get("reason"),
                )
                return
            logger.info(
                "Active download reconcile after infected handling: removed=%s updated=%s checked=%s",
                result["removed_count"],
                result.get("updated_count", 0),
                result["total_checked"],
            )
        except Exception as exc:
            logger.error(
                "Active download reconcile failed after infected handling: %s",
                exc,
                exc_info=True,
            )
