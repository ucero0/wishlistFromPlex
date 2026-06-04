"""Handle corrupt media: blacklist, remove from Deluge, retry with a new torrent."""
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
from app.domain.models.active_download import ActiveDownload
from app.domain.models.media_integrity_result import MediaIntegrityResult
from app.domain.ports.external.deluge.deluge_provider import DelugeProvider
from app.domain.services.manual_torrent_tracking import is_manual_active_download

logger = logging.getLogger(__name__)


class HandleCorruptMediaUseCase:
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
        integrity_result: MediaIntegrityResult,
    ) -> ScanAndIngestTorrentResult:
        logger.warning(
            "Corrupt media for '%s': %s",
            torrent_download.title,
            integrity_result.summary_message,
        )
        await self._add_torrent_to_blacklist_use_case.execute(
            torrent_download.prowlarr_guid,
            reason="corrupt",
            name=torrent_download.title,
            year=torrent_download.year,
            media_type=torrent_download.type,
        )
        deleted = await self._deluge_provider.remove_torrent(
            torrent_hash, remove_data=True
        )
        if is_manual_active_download(torrent_download):
            logger.info(
                "Manual Deluge torrent '%s' corrupt — blacklisted and removed, no retry",
                torrent_download.title,
            )
        else:
            outcome = await self._retry_active_download.execute(
                torrent_download, blacklist_reason="corrupt"
            )
            if outcome == RetryActiveDownloadOutcome.SUCCESS:
                logger.info(
                    "Queued replacement torrent for corrupt download '%s'",
                    torrent_download.title,
                )
            elif outcome == RetryActiveDownloadOutcome.DEFERRED:
                logger.info(
                    "Deferred replacement torrent for corrupt download '%s'",
                    torrent_download.title,
                )
            else:
                logger.warning(
                    "No replacement torrent queued for corrupt download '%s' (%s)",
                    torrent_download.title,
                    outcome.value,
                )
            await self._reconcile_active_downloads()

        return ScanAndIngestTorrentResult(
            status="corrupt",
            message=integrity_result.summary_message,
            infected=False,
            moved=False,
            deleted=deleted,
            corrupt_files=integrity_result.corrupt_files,
        )

    async def _reconcile_active_downloads(self) -> None:
        try:
            result = await self._reconcile_active_downloads_use_case.execute()
            if result.get("skipped"):
                logger.warning(
                    "Active download reconcile skipped after corrupt handling: reason=%s",
                    result.get("reason"),
                )
                return
            logger.info(
                "Active download reconcile after corrupt handling: removed=%s updated=%s checked=%s",
                result["removed_count"],
                result.get("updated_count", 0),
                result["total_checked"],
            )
        except Exception as exc:
            logger.error(
                "Active download reconcile failed after corrupt handling: %s",
                exc,
                exc_info=True,
            )
