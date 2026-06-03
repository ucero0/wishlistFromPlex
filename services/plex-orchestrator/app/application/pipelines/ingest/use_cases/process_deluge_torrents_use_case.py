"""Poll Deluge: ingest completed torrents, remove unhealthy ones, then sync tracking."""
import asyncio
import logging

from app.application.active_downloads.queries.get_active_download_queries import (
    GetAllActiveDownloadsQuery,
)
from app.application.deluge.queries.get_torrent_status_query import GetTorrentsStatusQuery
from app.application.pipelines.ingest.models.deluge_torrent_maintenance_result import (
    DelugeTorrentMaintenanceResult,
)
from app.application.pipelines.ingest.use_cases.handle_unhealthy_torrent_use_case import (
    HandleUnhealthyTorrentUseCase,
)
from app.application.pipelines.ingest.use_cases.scan_and_ingest_torrent_use_case import (
    ScanAndIngestTorrentUseCase,
)
from app.application.pipelines.watchlist.use_cases.reconcile_active_downloads_with_deluge_use_case import (
    ReconcileActiveDownloadsWithDelugeUseCase,
)
from app.application.plex.use_cases.refresh_plex_library_disk_stats_use_case import (
    RefreshPlexLibraryDiskStatsUseCase,
)
from app.application.settings.services.torrent_health_config_service import (
    TorrentHealthConfigService,
)
from app.core.config import settings
from app.domain.errors.deluge import DelugeConnectionError
from app.domain.models.active_download import ActiveDownload
from app.domain.models.torrent import Torrent
from app.domain.services.deluge_path_health import (
    probe_deluge_path_health,
    should_skip_unhealthy_removal,
)
from app.domain.services.torrent_health import (
    TorrentHealthThresholds,
    is_torrent_unhealthy,
)

logger = logging.getLogger(__name__)


def _normalize_hash(value: str) -> str:
    return (value or "").lower()


def _downloads_by_uid(active_downloads) -> dict[str, ActiveDownload]:
    return {_normalize_hash(row.uid): row for row in active_downloads}


class ProcessDelugeTorrentsUseCase:
    def __init__(
        self,
        get_torrents_status_query: GetTorrentsStatusQuery,
        get_all_active_downloads_query: GetAllActiveDownloadsQuery,
        scan_and_ingest_torrent_use_case: ScanAndIngestTorrentUseCase,
        handle_unhealthy_torrent_use_case: HandleUnhealthyTorrentUseCase,
        reconcile_active_downloads_use_case: ReconcileActiveDownloadsWithDelugeUseCase,
        refresh_disk_stats_use_case: RefreshPlexLibraryDiskStatsUseCase,
        torrent_health_config_service: TorrentHealthConfigService,
    ):
        self._get_torrents_status_query = get_torrents_status_query
        self._get_all_active_downloads_query = get_all_active_downloads_query
        self._scan_and_ingest = scan_and_ingest_torrent_use_case
        self._handle_unhealthy = handle_unhealthy_torrent_use_case
        self._reconcile = reconcile_active_downloads_use_case
        self._refresh_disk_stats = refresh_disk_stats_use_case
        self._torrent_health_config = torrent_health_config_service

    async def execute(self) -> DelugeTorrentMaintenanceResult:
        result = DelugeTorrentMaintenanceResult()
        try:
            deluge_torrents = await self._get_torrents_status_query.execute()
        except DelugeConnectionError as exc:
            logger.warning("Deluge maintenance skipped: %s", exc.message)
            return result

        active_downloads = await self._get_all_active_downloads_query.execute()
        downloads_by_uid = _downloads_by_uid(active_downloads)

        try:
            await self._refresh_disk_stats.execute()
            result.disk_stats_refreshed = True
        except Exception as exc:
            logger.warning(
                "Could not refresh library disk free space before ingest batch: %s", exc
            )

        await self._ingest_completed_torrents(
            deluge_torrents, downloads_by_uid, result
        )

        try:
            deluge_torrents = await self._get_torrents_status_query.execute()
        except DelugeConnectionError as exc:
            logger.warning(
                "Deluge unhealthy check skipped after ingest: %s", exc.message
            )
            reconcile_result = await self._reconcile.execute()
            result.tracking_updated = reconcile_result.get("updated_count", 0)
            result.tracking_removed = reconcile_result.get("removed_count", 0)
            return result

        active_downloads = await self._get_all_active_downloads_query.execute()
        await self._remove_unhealthy_torrents(
            deluge_torrents,
            _downloads_by_uid(active_downloads),
            result,
        )

        reconcile_result = await self._reconcile.execute()
        result.tracking_updated = reconcile_result.get("updated_count", 0)
        result.tracking_removed = reconcile_result.get("removed_count", 0)

        logger.info(
            "Deluge maintenance: completed=%s ingested=%s errors=%s "
            "disk_stats_refreshed=%s tracking_updated=%s tracking_removed=%s "
            "unhealthy_removed=%s vpn_healthy=%s unhealthy_skipped_vpn=%s skipped_no_db=%s",
            result.completed_checked,
            result.ingested,
            result.ingest_errors,
            result.disk_stats_refreshed,
            result.tracking_updated,
            result.tracking_removed,
            result.unhealthy_removed,
            result.vpn_healthy,
            result.unhealthy_skipped_vpn_unhealthy,
            result.skipped_no_active_download,
        )
        return result

    async def _ingest_completed_torrents(
        self,
        deluge_torrents: list[Torrent],
        downloads_by_uid: dict[str, ActiveDownload],
        result: DelugeTorrentMaintenanceResult,
    ) -> None:
        for torrent in deluge_torrents:
            active = downloads_by_uid.get(_normalize_hash(torrent.hash))
            if active is None:
                if torrent.is_finished:
                    result.skipped_no_active_download += 1
                continue
            if not torrent.is_finished:
                continue

            result.completed_checked += 1
            ingest_result = await self._scan_and_ingest.execute(torrent.hash)
            if ingest_result.status in ("clean", "infected", "pending_move"):
                result.ingested += 1
                logger.info(
                    "Ingest poll for '%s' (%s): %s",
                    active.title,
                    torrent.hash[:8],
                    ingest_result.status,
                )
            else:
                result.ingest_errors += 1
                logger.warning(
                    "Ingest poll failed for '%s' (%s): %s",
                    active.title,
                    torrent.hash[:8],
                    ingest_result.message,
                )

    async def _remove_unhealthy_torrents(
        self,
        deluge_torrents: list[Torrent],
        downloads_by_uid: dict[str, ActiveDownload],
        result: DelugeTorrentMaintenanceResult,
    ) -> bool:
        health_config = await self._torrent_health_config.get_config()
        path_health = await asyncio.to_thread(probe_deluge_path_health, settings)
        result.vpn_healthy = path_health.vpn_healthy

        if should_skip_unhealthy_removal(
            path_health,
            skip_when_vpn_down=health_config.skip_when_vpn_unhealthy,
        ):
            result.unhealthy_skipped_vpn_unhealthy = True
            logger.warning(
                "Skipping unhealthy torrent removal — VPN path unhealthy (%s). "
                "Fix Gluetun first; see GET /deluge/test-connection (vpn_healthy)",
                path_health.error,
            )
            return False

        strict = (
            health_config.use_strict_when_vpn_healthy and path_health.vpn_healthy
        )
        thresholds = TorrentHealthThresholds.from_config(health_config, strict=strict)
        if strict:
            logger.info("VPN path healthy; using strict unhealthy torrent thresholds")

        removed_any = False

        for torrent in deluge_torrents:
            if torrent.is_finished:
                continue
            active = downloads_by_uid.get(_normalize_hash(torrent.hash))
            if active is None:
                continue
            if not is_torrent_unhealthy(torrent, thresholds=thresholds):
                continue

            result.unhealthy_checked += 1
            removed = await self._handle_unhealthy.execute(
                torrent,
                active,
                thresholds=thresholds,
            )
            if removed:
                result.unhealthy_removed += 1
                removed_any = True

        return removed_any
