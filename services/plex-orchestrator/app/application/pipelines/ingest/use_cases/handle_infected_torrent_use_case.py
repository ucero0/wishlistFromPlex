"""Handle infected torrent: blacklist, remove from Deluge, re-add to watchlist."""
import logging

from app.application.blacklist_torrent.use_cases import AddTorrentToBlacklistUseCase
from app.application.pipelines.watchlist.use_cases.reconcile_active_downloads_with_deluge_use_case import (
    ReconcileActiveDownloadsWithDelugeUseCase,
)
from app.application.pipelines.ingest.models.scan_and_ingest_torrent_result import (
    ScanAndIngestTorrentResult,
)
from app.application.plex.use_cases.add_watchlist_item_use_case import AddWatchlistItemUseCase
from app.domain.models.scan_result import ScanResult
from app.domain.models.active_download import ActiveDownload
from app.domain.ports.external.deluge.deluge_provider import DelugeProvider

logger = logging.getLogger(__name__)


class HandleInfectedTorrentUseCase:
    def __init__(
        self,
        deluge_provider: DelugeProvider,
        add_torrent_to_blacklist_use_case: AddTorrentToBlacklistUseCase,
        add_watchlist_item_use_case: AddWatchlistItemUseCase,
        reconcile_active_downloads_use_case: ReconcileActiveDownloadsWithDelugeUseCase,
    ):
        self._deluge_provider = deluge_provider
        self._add_torrent_to_blacklist_use_case = add_torrent_to_blacklist_use_case
        self._add_watchlist_item_use_case = add_watchlist_item_use_case
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
        await self._try_readd_to_watchlist(torrent_download)
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

    async def _try_readd_to_watchlist(self, torrent_download: ActiveDownload) -> None:
        if not torrent_download.watchlist_item_id:
            logger.warning(
                "RatingKey not available for %s (plex_guid: %s). Cannot add back to watchlist.",
                torrent_download.title,
                torrent_download.plex_guid,
            )
            return
        if not torrent_download.plex_user_token:
            logger.warning(
                "Plex user token not available for %s (plex_guid: %s). Cannot add back to watchlist.",
                torrent_download.title,
                torrent_download.plex_guid,
            )
            return
        try:
            await self._add_watchlist_item_use_case.execute(
                torrent_download.watchlist_item_id,
                torrent_download.plex_user_token,
            )
            logger.info(
                "Added %s back to watchlist for re-download", torrent_download.title
            )
        except Exception as exc:
            logger.error("Error adding item back to watchlist: %s", exc, exc_info=True)

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
