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
from app.application.blacklist_torrent.use_cases import AddTorrentToBlacklistUseCase
from app.application.plex.useCases.addWatchListItem import AddWatchListItemUseCase
from app.application.plex.useCases.partialScanLibrary import PartialScanLibraryUseCase
from app.domain.models.antivirusScan import AntivirusScan
from app.domain.models.media import MediaType
from app.domain.models.scanResult import ScanResult
from app.domain.models.torrentDownload import TorrentDownload
from app.domain.ports.external.deluge.delugeProvider import DelugeProvider
from app.domain.ports.external.plex.plex_section_resolver import PlexSectionResolverPort
from app.domain.ports.repositories.antivirus.antivirusRepo import AntivirusRepoPort
from app.domain.services.filesystem_service import FilesystemService

logger = logging.getLogger(__name__)


class AntivirusScanTorrentAndIngestResult(BaseModel):
    """
    Result of this use case: error, infected, or clean (with optional move/scan details).
    """

    status: str  # "error" | "infected" | "clean"
    message: Optional[str] = None
    infected: bool = False
    moved: Optional[bool] = None
    deleted: Optional[bool] = None
    destination_path: Optional[str] = None
    virus_name: Optional[str] = None
    infected_files: Optional[List[str]] = None
    yara_matches: Optional[List[str]] = None
    scanned_files: Optional[List[str]] = None

    class Config:
        frozen = False


class AntivirusScanTorrentAndIngestUseCase:
    """
    Runs antivirus scan (via AntivirusScanTorrentUseCase); if clean, moves to media and triggers Plex.
    If infected, removes torrent and re-adds item to watchlist.
    """

    def __init__(
        self,
        antivirus_scan_torrent_use_case: AntivirusScanTorrentUseCase,
        filesystem_service: FilesystemService,
        antivirus_repo: AntivirusRepoPort,
        deluge_provider: DelugeProvider,
        add_torrent_to_blacklist_use_case: AddTorrentToBlacklistUseCase,
        add_watchlist_item_use_case: AddWatchListItemUseCase,
        partial_scan_library_use_case: PartialScanLibraryUseCase,
        plex_section_resolver: PlexSectionResolverPort,
    ):
        self._antivirus_scan_torrent_use_case = antivirus_scan_torrent_use_case
        self._filesystem_service = filesystem_service
        self._antivirus_repo = antivirus_repo
        self._deluge_provider = deluge_provider
        self._add_torrent_to_blacklist_use_case = add_torrent_to_blacklist_use_case
        self._add_watchlist_item_use_case = add_watchlist_item_use_case
        self._partial_scan_library_use_case = partial_scan_library_use_case
        self._plex_section_resolver = plex_section_resolver

    async def execute(self, torrent_hash: str) -> AntivirusScanTorrentAndIngestResult:
        """Antivirus scan torrent, then if clean: move + Plex; if infected: remove torrent + watchlist."""
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
    ) -> AntivirusScanTorrentAndIngestResult:
        destination_path = self._resolve_destination_path(
            torrent_download, scan_path, is_file
        )
        moved = self._filesystem_service.move(scan_path, destination_path)

        if moved:
            await self._deluge_provider.remove_torrent(torrent_hash, remove_data=False)
            await self._update_scan_with_destination(
                scan_record, destination_path, is_file
            )
            await self._trigger_partial_scan(
                torrent_download.plexUserToken,
                torrent_download.type,
                destination_path,
                is_file,
            )

        return AntivirusScanTorrentAndIngestResult(
            status="clean",
            message="Files scanned and moved successfully",
            infected=False,
            scanned_files=scanned_files,
            moved=moved,
            destination_path=destination_path if moved else None,
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

    def _resolve_destination_path(
        self, torrent_download: TorrentDownload, scan_path: str, is_file: bool
    ) -> str:
        media_type = torrent_download.type
        base_path = self._filesystem_service.get_media_destination_path(
            media_type, torrent_download.fileName
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
            destination = Path(base_path)

        return str(destination)

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

    async def _update_scan_with_destination(
        self, scan_record: AntivirusScan, destination_path: str, is_file: bool
    ) -> None:
        if is_file:
            scan_record.filePath = destination_path
        else:
            scan_record.folderPathDst = destination_path
        await self._antivirus_repo.update(scan_record)

    async def _trigger_partial_scan(
        self,
        user_token: Optional[str],
        media_type: str,
        destination_path: str,
        is_file: bool,
    ) -> None:
        if not user_token:
            logger.warning("Plex user token not available, skipping partial scan")
            return

        section_id = self._plex_section_resolver.get_section_id_for_media_type(
            media_type
        )
        if section_id is None:
            logger.warning(
                f"Unknown media type: {media_type}, skipping partial scan"
            )
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
                f"Successfully triggered partial scan for {media_type} at {folder_path}"
            )
        except Exception as e:
            logger.error(f"Error triggering partial scan: {e}", exc_info=True)

    def _folder_path_for_plex_scan(self, destination_path: str, is_file: bool) -> str:
        if is_file:
            return str(Path(destination_path).parent)
        return destination_path
