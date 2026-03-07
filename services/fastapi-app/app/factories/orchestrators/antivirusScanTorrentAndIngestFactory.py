"""Factory for AntivirusScanTorrentUseCase and AntivirusScanTorrentAndIngestUseCase (orchestrator)."""
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from app.infrastructure.persistence.database import get_db
from app.infrastructure.persistence.antivirus.repo.antivirus_repository import (
    AntivirusRepository,
)
from app.infrastructure.externalApis.antivirus.client import AntivirusClient
from app.adapters.external.antivirus.adapter import AntivirusAdapter
from app.domain.services.filesystem_service import FilesystemServiceImpl
from app.application.orchestrators.useCases.antivirusScanTorrent import AntivirusScanTorrentUseCase
from app.application.orchestrators.useCases.antivirusScanTorrentAndIngest import (
    AntivirusScanTorrentAndIngestUseCase,
)
from app.factories.torrentDownload.torrentDownloadFactory import (
    create_get_torrent_download_by_uid_query,
)
from app.infrastructure.externalApis.deluge.client import DelugeClient
from app.adapters.external.deluge.adapter import DelugeAdapter
from app.factories.plex.plexWatchListFactory import createAddWatchListItemUseCase
from app.factories.plex.plexServerFactory import createPartialScanLibraryUseCase
from app.infrastructure.config.plex_section_resolver import PlexSectionResolverAdapter


def _get_antivirus_repo(session: AsyncSession) -> AntivirusRepository:
    return AntivirusRepository(session)


def create_antivirus_scan_torrent_use_case(
    session: AsyncSession = Depends(get_db)
) -> AntivirusScanTorrentUseCase:
    """Build AntivirusScanTorrentUseCase: resolve torrent path, antivirus scan, persist record (no move/Plex)."""
    return AntivirusScanTorrentUseCase(
        get_torrent_download_query=create_get_torrent_download_by_uid_query(session),
        filesystem_service=FilesystemServiceImpl(),
        antivirus_provider=AntivirusAdapter(AntivirusClient()),
        antivirus_repo=_get_antivirus_repo(session),
    )


def create_antivirus_scan_torrent_and_ingest_use_case(
    session: AsyncSession = Depends(get_db)
) -> AntivirusScanTorrentAndIngestUseCase:
    """Build AntivirusScanTorrentAndIngestUseCase: antivirus scan torrent then ingest (move + Deluge + Plex)."""
    antivirus_scan_torrent_use_case = create_antivirus_scan_torrent_use_case(session)
    filesystem_service = FilesystemServiceImpl()
    antivirus_repo = _get_antivirus_repo(session)
    deluge_client = DelugeClient()
    deluge_adapter = DelugeAdapter(deluge_client)
    add_watchlist_item_use_case = createAddWatchListItemUseCase()
    partial_scan_library_use_case = createPartialScanLibraryUseCase()
    plex_section_resolver = PlexSectionResolverAdapter()

    return AntivirusScanTorrentAndIngestUseCase(
        antivirus_scan_torrent_use_case=antivirus_scan_torrent_use_case,
        filesystem_service=filesystem_service,
        antivirus_repo=antivirus_repo,
        deluge_provider=deluge_adapter,
        add_watchlist_item_use_case=add_watchlist_item_use_case,
        partial_scan_library_use_case=partial_scan_library_use_case,
        plex_section_resolver=plex_section_resolver,
    )
