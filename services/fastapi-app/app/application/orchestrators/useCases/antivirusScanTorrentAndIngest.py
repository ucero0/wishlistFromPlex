"""
Orchestrator: after antivirus scan of torrent, ingest (move to Plex library) or handle infection.

Uses AntivirusScanTorrentUseCase for virus check only; then move, Deluge, Plex.
"""
import logging
from pathlib import Path
from typing import Optional, List

from pydantic import BaseModel
from app.application.orchestrators.useCases.antivirusScanTorrent import (
    AntivirusScanTorrentUseCase,
)
from app.application.torrentDownload.queries.getTorrentDownload import (
    GetTorrentDownloadByUidQuery,
)
from app.application.blacklist_torrent.use_cases import AddTorrentToBlacklistUseCase
from app.domain.models.antivirus_scan_status import (
    is_file_scan,
    scan_path_from_record,
)
from app.application.plex.useCases.addWatchListItem import AddWatchListItemUseCase
from app.application.plex.useCases.partialScanLibrary import PartialScanLibraryUseCase
from app.application.plex.useCases.syncPlexLibraryPaths import (
    SyncPlexLibraryPathsFromServerUseCase,
)
from app.domain.models.antivirusScan import AntivirusScan
from app.domain.models.media import MediaType
from app.domain.models.scanResult import ScanResult
from app.domain.models.torrentDownload import TorrentDownload
from app.domain.ports.external.deluge.delugeProvider import DelugeProvider
from app.domain.errors.plex import (
    PlexLibraryPathNoSpaceError,
    PlexLibraryPathNotConfiguredError,
)
from app.domain.ports.repositories.antivirus.antivirusRepo import AntivirusRepoPort
from app.domain.services.filesystem_service import FilesystemService
from app.domain.services.plex_library_destination_selector import (
    PlexLibraryDestinationSelector,
)

logger = logging.getLogger(__name__)


class AntivirusScanTorrentAndIngestResult(BaseModel):
    """
    Result of this use case: error, infected, or clean (with optional move/scan details).
    """

    status: str  # "error" | "infected" | "clean" | "pending_move"
    message: Optional[str] = None
    infected: bool = False
    scan_skipped: bool = False
    moved: Optional[bool] = None
    deleted: Optional[bool] = None
    destination_path: Optional[str] = None
    virus_name: Optional[str] = None
    infected_files: Optional[List[str]] = None
    yara_matches: Optional[List[str]] = None
    scanned_files: Optional[List[str]] = None
    ingest_error: Optional[str] = None
    planned_destination: Optional[str] = None

    class Config:
        frozen = False


class AntivirusScanTorrentAndIngestUseCase:
    """
    Runs antivirus scan (via AntivirusScanTorrentUseCase); if clean, moves to media and triggers Plex.
    If infected, removes torrent and re-adds item to watchlist.
    """

    def __init__(
        self,
        get_torrent_download_query: GetTorrentDownloadByUidQuery,
        antivirus_scan_torrent_use_case: AntivirusScanTorrentUseCase,
        filesystem_service: FilesystemService,
        antivirus_repo: AntivirusRepoPort,
        deluge_provider: DelugeProvider,
        add_torrent_to_blacklist_use_case: AddTorrentToBlacklistUseCase,
        add_watchlist_item_use_case: AddWatchListItemUseCase,
        partial_scan_library_use_case: PartialScanLibraryUseCase,
        destination_selector: PlexLibraryDestinationSelector,
        sync_library_paths_use_case: SyncPlexLibraryPathsFromServerUseCase,
    ):
        self._get_torrent_download_query = get_torrent_download_query
        self._antivirus_scan_torrent_use_case = antivirus_scan_torrent_use_case
        self._filesystem_service = filesystem_service
        self._antivirus_repo = antivirus_repo
        self._deluge_provider = deluge_provider
        self._add_torrent_to_blacklist_use_case = add_torrent_to_blacklist_use_case
        self._add_watchlist_item_use_case = add_watchlist_item_use_case
        self._partial_scan_library_use_case = partial_scan_library_use_case
        self._destination_selector = destination_selector
        self._sync_library_paths = sync_library_paths_use_case

    async def execute(self, torrent_hash: str) -> AntivirusScanTorrentAndIngestResult:
        """Antivirus scan torrent, then if clean: move + Plex; if infected: remove torrent + watchlist."""
        torrent_download = await self._get_torrent_download_query.execute(torrent_hash)
        if not torrent_download:
            return AntivirusScanTorrentAndIngestResult(
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
                return await self._ingest_clean(
                    torrent_hash,
                    torrent_download,
                    pending,
                    record_path,
                    is_file_scan(pending),
                    scanned_files=[],
                    scan_skipped=True,
                )
            if record_path:
                return AntivirusScanTorrentAndIngestResult(
                    status="error",
                    message=f"Quarantine path no longer exists: {record_path}",
                    infected=False,
                    moved=False,
                    scan_skipped=True,
                )

        scan_result = await self._antivirus_scan_torrent_use_case.execute(torrent_hash)

        if scan_result.status == "error":
            return AntivirusScanTorrentAndIngestResult(
                status="error",
                message=scan_result.message,
                infected=False,
                moved=False,
            )

        if scan_result.infected and scan_result.scan_result and scan_result.torrent_download:
            return await self._handle_infected(
                torrent_hash, scan_result.torrent_download, scan_result.scan_result
            )

        if (
            scan_result.scan_record
            and scan_result.scan_path is not None
            and scan_result.is_file is not None
            and scan_result.torrent_download
        ):
            return await self._ingest_clean(
                torrent_hash,
                scan_result.torrent_download,
                scan_result.scan_record,
                scan_result.scan_path,
                scan_result.is_file,
                scan_result.scan_result.scanned_files if scan_result.scan_result else [],
                scan_skipped=False,
            )

        return AntivirusScanTorrentAndIngestResult(
            status="error",
            message="Scan succeeded but missing data for ingest",
            infected=False,
            moved=False,
        )

    async def _handle_infected(
        self,
        torrent_hash: str,
        torrent_download: TorrentDownload,
        scan_result: ScanResult,
    ) -> AntivirusScanTorrentAndIngestResult:
        logger.warning(
            f"Infected files found: {scan_result.infected_files}"
        )
        await self._add_torrent_to_blacklist_use_case.execute(
            torrent_download.guidProwlarr,
            reason="infected",
            name=torrent_download.title,
            year=torrent_download.year,
            media_type=torrent_download.type,
        )
        deleted = await self._deluge_provider.remove_torrent(
            torrent_hash, remove_data=True
        )
        await self._try_readd_to_watchlist(torrent_download)
        return AntivirusScanTorrentAndIngestResult(
            status="infected",
            message=f"Found {len(scan_result.infected_files)} infected files",
            infected=True,
            virus_name=scan_result.virus_name,
            infected_files=scan_result.infected_files,
            yara_matches=scan_result.yara_matches,
            scanned_files=scan_result.scanned_files,
            deleted=deleted,
        )

    async def _ingest_clean(
        self,
        torrent_hash: str,
        torrent_download: TorrentDownload,
        scan_record: AntivirusScan,
        scan_path: str,
        is_file: bool,
        scanned_files: list,
        scan_skipped: bool = False,
    ) -> AntivirusScanTorrentAndIngestResult:
        destination_path: str | None = None
        section_id: int | None = None
        try:
            if torrent_download.plexUserToken:
                try:
                    await self._sync_library_paths.execute(
                        torrent_download.plexUserToken
                    )
                except Exception as exc:
                    logger.warning(
                        "Could not refresh Plex library paths before ingest: %s",
                        exc,
                    )
            destination_path, section_id = await self._resolve_destination_path(
                torrent_download, scan_path, is_file
            )
        except (PlexLibraryPathNotConfiguredError, PlexLibraryPathNoSpaceError) as exc:
            error_detail = str(exc.message)
            await self._record_ingest_failure(
                scan_record, error_detail, destination_path
            )
            return AntivirusScanTorrentAndIngestResult(
                status="pending_move",
                message=error_detail,
                infected=False,
                moved=False,
                scan_skipped=scan_skipped,
                ingest_error=error_detail,
                planned_destination=destination_path,
            )

        moved = self._filesystem_service.move(scan_path, destination_path)

        if moved:
            await self._deluge_provider.remove_torrent(torrent_hash, remove_data=False)
            await self._update_scan_with_destination(
                scan_record, destination_path, is_file, clear_ingest_error=True
            )
            await self._trigger_partial_scan(
                torrent_download.plexUserToken,
                section_id,
                destination_path,
                is_file,
            )

        if moved:
            message = (
                "Moved to library (antivirus scan skipped, already clean)"
                if scan_skipped
                else "Files scanned and moved successfully"
            )
            status = "clean"
        else:
            move_error = self._filesystem_service.explain_move_failure(
                scan_path, destination_path
            )
            await self._record_ingest_failure(
                scan_record, move_error, destination_path
            )
            status = "pending_move"
            message = move_error

        return AntivirusScanTorrentAndIngestResult(
            status=status,
            message=message,
            infected=False,
            scanned_files=scanned_files if not scan_skipped else None,
            scan_skipped=scan_skipped,
            moved=moved,
            destination_path=destination_path if moved else None,
            ingest_error=None if moved else message,
            planned_destination=None if moved else destination_path,
        )

    async def _try_readd_to_watchlist(self, torrent_download: TorrentDownload) -> None:
        if not torrent_download.ratingKey:
            logger.warning(
                f"RatingKey not available for {torrent_download.title} "
                f"(guidPlex: {torrent_download.guidPlex}). Cannot add back to watchlist."
            )
            return
        if not torrent_download.plexUserToken:
            logger.warning(
                f"Plex user token not available for {torrent_download.title} "
                f"(guidPlex: {torrent_download.guidPlex}). Cannot add back to watchlist."
            )
            return
        try:
            await self._add_watchlist_item_use_case.execute(
                torrent_download.ratingKey, torrent_download.plexUserToken
            )
            logger.info(
                f"Added {torrent_download.title} back to watchlist for re-download"
            )
        except Exception as e:
            logger.error(f"Error adding item back to watchlist: {e}", exc_info=True)

    async def _resolve_destination_path(
        self, torrent_download: TorrentDownload, scan_path: str, is_file: bool
    ) -> tuple[str, int]:
        media_type = torrent_download.type
        required_bytes = self._filesystem_service.get_path_size_bytes(scan_path)
        library_root = await self._destination_selector.select(
            media_type, required_bytes
        )
        section_id = int(library_root.section_id)

        base_path = str(
            Path(library_root.path) / torrent_download.fileName
        )
        destination = Path(base_path)
        parent = destination.parent
        show_or_movie_folder = self._media_folder_name(torrent_download)

        if self._is_movie(media_type):
            if is_file:
                destination = parent / show_or_movie_folder / destination.name
            else:
                destination = parent / show_or_movie_folder
        elif self._is_show(media_type):
            season_num = torrent_download.season if torrent_download.season else 1
            season_folder = self._season_folder_name(season_num)
            if is_file:
                destination = (
                    parent / show_or_movie_folder / season_folder / destination.name
                )
            else:
                destination = parent / show_or_movie_folder / season_folder
        else:
            if is_file:
                destination = parent / show_or_movie_folder / destination.name
            else:
                destination = parent / show_or_movie_folder

        return str(destination), section_id

    def _is_movie(self, media_type: str) -> bool:
        return media_type.lower() == MediaType.MOVIE.value

    def _is_show(self, media_type: str) -> bool:
        normalized = media_type.lower()
        return normalized in (MediaType.SHOW.value, MediaType.TVSHOW.value)

    def _media_folder_name(self, torrent_download: TorrentDownload) -> str:
        if torrent_download.year:
            return f"{torrent_download.title} ({torrent_download.year})"
        return torrent_download.title

    def _season_folder_name(self, season_num: int) -> str:
        return f"Season {season_num:02d}"

    async def _record_ingest_failure(
        self,
        scan_record: AntivirusScan,
        error: str,
        planned_destination: str | None,
    ) -> None:
        scan_record.ingestError = error
        scan_record.plannedDestination = planned_destination
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
            scan_record.filePath = destination_path
        else:
            scan_record.folderPathDst = destination_path
        if clear_ingest_error:
            scan_record.ingestError = None
            scan_record.plannedDestination = None
        await self._antivirus_repo.update(scan_record)

    async def _trigger_partial_scan(
        self,
        user_token: Optional[str],
        section_id: int,
        destination_path: str,
        is_file: bool,
    ) -> None:
        if not user_token:
            logger.warning("Plex user token not available, skipping partial scan")
            return

        folder_path = self._folder_path_for_plex_scan(destination_path, is_file)
        try:
            logger.info(
                f"Triggering partial scan for section {section_id}, folder: {folder_path}"
            )
            await self._partial_scan_library_use_case.execute(
                user_token=user_token,
                section_id=section_id,
                folder_path=folder_path,
            )
            logger.info(
                "Successfully triggered partial scan for section %s at %s",
                section_id,
                folder_path,
            )
        except Exception as e:
            logger.error(f"Error triggering partial scan: {e}", exc_info=True)

    def _folder_path_for_plex_scan(self, destination_path: str, is_file: bool) -> str:
        if is_file:
            return str(Path(destination_path).parent)
        return destination_path
