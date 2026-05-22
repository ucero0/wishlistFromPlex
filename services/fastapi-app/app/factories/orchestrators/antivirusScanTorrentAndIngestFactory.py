"""Factory for AntivirusScanTorrentUseCase and AntivirusScanTorrentAndIngestUseCase (orchestrator)."""
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from app.infrastructure.persistence.database import get_db
from app.infrastructure.persistence.antivirus.repo.antivirus_repository import (
    AntivirusRepository,
)
from app.infrastructure.externalApis.antivirus.client import AntivirusClient
from app.adapters.external.antivirus.adapter import AntivirusAdapter
from app.composition.infrastructure_services import build_filesystem_service
from app.application.orchestrators.useCases.antivirusScanTorrent import AntivirusScanTorrentUseCase
from app.application.orchestrators.useCases.antivirusScanTorrentAndIngest import (
    AntivirusScanTorrentAndIngestUseCase,
)
from app.factories.torrentDownload.torrentDownloadFactory import (
    create_get_torrent_download_by_uid_query,
)
from app.infrastructure.externalApis.deluge.client import DelugeClient
from app.adapters.external.deluge.adapter import DelugeAdapter
from app.factories.blacklist_torrent import create_add_torrent_to_blacklist_use_case
from app.factories.plex.plexWatchListFactory import createAddWatchListItemUseCase
from app.factories.plex.plexServerFactory import createPartialScanLibraryUseCase
from app.composition.plex_library_paths import build_sync_plex_library_paths_use_case
from app.factories.plex.plexLibraryPathFactory import (
    create_plex_library_destination_selector_for_session,
)


def _get_antivirus_repo(session: AsyncSession) -> AntivirusRepository:
    return AntivirusRepository(session)


def create_antivirus_scan_torrent_use_case(
    session: AsyncSession = Depends(get_db)
) -> AntivirusScanTorrentUseCase:
    """Build AntivirusScanTorrentUseCase: resolve torrent path, antivirus scan, persist record (no move/Plex)."""
    return AntivirusScanTorrentUseCase(
        get_torrent_download_query=create_get_torrent_download_by_uid_query(session),
        filesystem_service=build_filesystem_service(),
        antivirus_provider=AntivirusAdapter(AntivirusClient()),
        antivirus_repo=_get_antivirus_repo(session),
    )


def create_antivirus_scan_torrent_and_ingest_use_case(
    session: AsyncSession = Depends(get_db)
) -> AntivirusScanTorrentAndIngestUseCase:
    """Build AntivirusScanTorrentAndIngestUseCase: antivirus scan torrent then ingest (move + Deluge + Plex)."""
    antivirus_scan_torrent_use_case = create_antivirus_scan_torrent_use_case(session)
    filesystem_service = build_filesystem_service()
    antivirus_repo = _get_antivirus_repo(session)
    deluge_client = DelugeClient()
    deluge_adapter = DelugeAdapter(deluge_client)
    add_torrent_to_blacklist_use_case = create_add_torrent_to_blacklist_use_case(session)
    add_watchlist_item_use_case = createAddWatchListItemUseCase()
    partial_scan_library_use_case = createPartialScanLibraryUseCase()
    destination_selector = create_plex_library_destination_selector_for_session(session)
    sync_library_paths = build_sync_plex_library_paths_use_case(session)

    return AntivirusScanTorrentAndIngestUseCase(
        get_torrent_download_query=create_get_torrent_download_by_uid_query(session),
        antivirus_scan_torrent_use_case=antivirus_scan_torrent_use_case,
        filesystem_service=filesystem_service,
        antivirus_repo=antivirus_repo,
        deluge_provider=deluge_adapter,
        add_torrent_to_blacklist_use_case=add_torrent_to_blacklist_use_case,
        add_watchlist_item_use_case=add_watchlist_item_use_case,
        partial_scan_library_use_case=partial_scan_library_use_case,
        destination_selector=destination_selector,
        sync_library_paths_use_case=sync_library_paths,
    )
