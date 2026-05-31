"""Move a clean scanned torrent into the Plex library and trigger partial scan."""
import logging
from typing import List

from app.application.pipelines.ingest.models.scan_and_ingest_torrent_result import (
    ScanAndIngestTorrentResult,
)
from app.application.pipelines.watchlist.use_cases.reconcile_active_downloads_with_deluge_use_case import (
    ReconcileActiveDownloadsWithDelugeUseCase,
)
from app.application.pipelines.watchlist.use_cases.remove_watchlist_entry_use_case import (
    RemoveWatchlistEntryUseCase,
)
from app.application.plex.use_cases.partial_scan_library_use_case import PartialScanLibraryUseCase
from app.application.plex.use_cases.refresh_plex_library_disk_stats_use_case import (
    RefreshPlexLibraryDiskStatsUseCase,
)
from app.application.plex.use_cases.sync_plex_library_paths_use_case import (
    SyncPlexLibraryPathsFromServerUseCase,
)
from app.domain.errors.plex import (
    PlexLibraryPathNoSpaceError,
    PlexLibraryPathNotConfiguredError,
)
from app.domain.models.antivirus_scan import AntivirusScan
from app.domain.models.active_download import ActiveDownload
from app.domain.ports.external.deluge.deluge_provider import DelugeProvider
from app.domain.ports.repositories.antivirus.antivirus_repository_port import AntivirusRepoPort
from app.domain.services.filesystem_service import FilesystemService
from app.domain.services.ingest_destination_resolver import IngestDestinationResolver
from app.domain.services.plex_library_destination_selector import (
    PlexLibraryDestinationSelector,
)

logger = logging.getLogger(__name__)


class IngestCleanTorrentUseCase:
    def __init__(
        self,
        filesystem_service: FilesystemService,
        antivirus_repo: AntivirusRepoPort,
        deluge_provider: DelugeProvider,
        destination_selector: PlexLibraryDestinationSelector,
        destination_resolver: IngestDestinationResolver,
        partial_scan_library_use_case: PartialScanLibraryUseCase,
        sync_library_paths_use_case: SyncPlexLibraryPathsFromServerUseCase,
        refresh_disk_stats_use_case: RefreshPlexLibraryDiskStatsUseCase,
        reconcile_active_downloads_use_case: ReconcileActiveDownloadsWithDelugeUseCase,
        remove_watchlist_entry_use_case: RemoveWatchlistEntryUseCase,
    ):
        self._filesystem_service = filesystem_service
        self._antivirus_repo = antivirus_repo
        self._deluge_provider = deluge_provider
        self._destination_selector = destination_selector
        self._destination_resolver = destination_resolver
        self._partial_scan_library_use_case = partial_scan_library_use_case
        self._sync_library_paths = sync_library_paths_use_case
        self._refresh_disk_stats = refresh_disk_stats_use_case
        self._reconcile_active_downloads_use_case = reconcile_active_downloads_use_case
        self._remove_watchlist_entry_use_case = remove_watchlist_entry_use_case

    async def execute(
        self,
        torrent_hash: str,
        torrent_download: ActiveDownload,
        scan_record: AntivirusScan,
        scan_path: str,
        is_file: bool,
        scanned_files: List[str],
        *,
        scan_skipped: bool = False,
    ) -> ScanAndIngestTorrentResult:
        destination_path: str | None = None
        section_id: int | None = None
        ingest_scan_path = scan_path
        ingest_is_file = is_file
        if not is_file:
            video_files = self._filesystem_service.list_video_files(scan_path)
            if len(video_files) == 1:
                ingest_scan_path = video_files[0]
                ingest_is_file = True
        try:
            try:
                await self._sync_library_paths.execute()
            except Exception as exc:
                logger.warning(
                    "Could not refresh Plex library paths before ingest: %s", exc
                )
            try:
                await self._refresh_disk_stats.execute()
            except Exception as exc:
                logger.warning(
                    "Could not refresh library disk free space before ingest: %s", exc
                )
            destination_path, section_id = await self._resolve_destination(
                torrent_download, ingest_scan_path, ingest_is_file
            )
        except (PlexLibraryPathNotConfiguredError, PlexLibraryPathNoSpaceError) as exc:
            error_detail = str(exc.message)
            await self._record_ingest_failure(
                scan_record, error_detail, destination_path
            )
            return ScanAndIngestTorrentResult(
                status="pending_move",
                message=error_detail,
                infected=False,
                moved=False,
                scan_skipped=scan_skipped,
                ingest_error=error_detail,
                planned_destination=destination_path,
            )

        moved = self._filesystem_service.move(ingest_scan_path, destination_path)
        if moved and not ingest_is_file:
            renamed = self._destination_resolver.apply_plex_media_names(
                destination_path,
                torrent_download,
                list_video_files=self._filesystem_service.list_video_files,
                rename_file=self._filesystem_service.move_file,
            )
            if renamed:
                logger.info(
                    "Renamed %s media file(s) under %s to Plex naming",
                    renamed,
                    destination_path,
                )
        if moved:
            await self._maybe_remove_watchlist_after_move(torrent_download)
            await self._deluge_provider.remove_torrent(torrent_hash, remove_data=False)
            await self._update_scan_with_destination(
                scan_record, destination_path, ingest_is_file, clear_ingest_error=True
            )
            await self._trigger_partial_scan(
                section_id,
                destination_path,
                ingest_is_file,
            )
            await self._reconcile_active_downloads()

        if moved:
            message = (
                "Moved to library (antivirus scan skipped, already clean)"
                if scan_skipped
                else "Files scanned and moved successfully"
            )
            status = "clean"
            ingest_error = None
            planned_destination = None
        else:
            move_error = self._filesystem_service.explain_move_failure(
                ingest_scan_path, destination_path
            )
            await self._record_ingest_failure(
                scan_record, move_error, destination_path
            )
            status = "pending_move"
            message = move_error
            ingest_error = move_error
            planned_destination = destination_path

        return ScanAndIngestTorrentResult(
            status=status,
            message=message,
            infected=False,
            scanned_files=scanned_files if not scan_skipped else None,
            scan_skipped=scan_skipped,
            moved=moved,
            destination_path=destination_path if moved else None,
            ingest_error=ingest_error,
            planned_destination=planned_destination,
        )

    async def _resolve_destination(
        self, torrent_download: ActiveDownload, scan_path: str, is_file: bool
    ) -> tuple[str, int]:
        required_bytes = self._filesystem_service.get_path_size_bytes(scan_path)
        library_root = await self._destination_selector.select(
            torrent_download.type, required_bytes
        )
        section_id = int(library_root.section_id)
        destination_path = self._destination_resolver.resolve(
            library_root.path,
            torrent_download,
            scan_path,
            is_file,
        )
        return destination_path, section_id

    async def _record_ingest_failure(
        self,
        scan_record: AntivirusScan,
        error: str,
        planned_destination: str | None,
    ) -> None:
        scan_record.ingest_error = error
        scan_record.planned_destination_path = planned_destination
        await self._antivirus_repo.update(scan_record)
        logger.warning(
            "Ingest pending for guid %s: %s (planned: %s)",
            scan_record.prowlarr_guid,
            error,
            planned_destination,
        )

    async def _update_scan_with_destination(
        self,
        scan_record: AntivirusScan,
        destination_path: str,
        is_file: bool,
        *,
        clear_ingest_error: bool = False,
    ) -> None:
        if is_file:
            scan_record.file_path = destination_path
        else:
            scan_record.destination_folder_path = destination_path
        if clear_ingest_error:
            scan_record.ingest_error = None
            scan_record.planned_destination_path = None
        await self._antivirus_repo.update(scan_record)

    async def _trigger_partial_scan(
        self,
        section_id: int,
        destination_path: str,
        is_file: bool,
    ) -> None:
        folder_path = self._destination_resolver.folder_path_for_plex_scan(
            destination_path, is_file
        )
        try:
            logger.info(
                "Triggering partial scan for section %s, folder: %s",
                section_id,
                folder_path,
            )
            await self._partial_scan_library_use_case.execute(
                section_id=section_id,
                folder_path=folder_path,
            )
            logger.info(
                "Successfully triggered partial scan for section %s at %s",
                section_id,
                folder_path,
            )
        except Exception as exc:
            logger.error("Error triggering partial scan: %s", exc, exc_info=True)

    async def _maybe_remove_watchlist_after_move(
        self, torrent_download: ActiveDownload
    ) -> None:
        if torrent_download.type in ("show", "tvshow"):
            return
        try:
            await self._remove_watchlist_entry_use_case.execute_from_active_download(
                torrent_download
            )
        except Exception as exc:
            logger.error(
                "Failed to remove watchlist entry for '%s' after ingest: %s",
                torrent_download.title,
                exc,
                exc_info=True,
            )

    async def _reconcile_active_downloads(self) -> None:
        """Drop DB rows for torrents no longer in Deluge (e.g. after successful ingest)."""
        try:
            result = await self._reconcile_active_downloads_use_case.execute()
            if result.get("skipped"):
                logger.warning(
                    "Active download reconcile skipped after ingest: reason=%s",
                    result.get("reason"),
                )
                return
            logger.info(
                "Active download reconcile after ingest: removed=%s updated=%s checked=%s",
                result["removed_count"],
                result.get("updated_count", 0),
                result["total_checked"],
            )
        except Exception as exc:
            logger.error(
                "Active download reconcile failed after ingest: %s",
                exc,
                exc_info=True,
            )
