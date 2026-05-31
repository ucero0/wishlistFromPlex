"""Composition root for scan-and-ingest pipeline."""
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.pipelines.ingest.use_cases.handle_infected_torrent_use_case import (
    HandleInfectedTorrentUseCase,
)
from app.application.pipelines.ingest.use_cases.ingest_clean_torrent_use_case import (
    IngestCleanTorrentUseCase,
)
from app.application.pipelines.ingest.use_cases.handle_unhealthy_torrent_use_case import (
    HandleUnhealthyTorrentUseCase,
)
from app.application.pipelines.ingest.use_cases.process_deluge_torrents_use_case import (
    ProcessDelugeTorrentsUseCase,
)
from app.application.pipelines.ingest.use_cases.scan_and_ingest_torrent_use_case import (
    ScanAndIngestTorrentUseCase,
)
from app.application.pipelines.ingest.use_cases.scan_torrent_use_case import (
    ScanTorrentUseCase,
)
from app.composition.antivirus import build_antivirus_provider
from app.composition.blacklist_torrent import build_add_torrent_to_blacklist_use_case
from app.composition.deluge import build_deluge_adapter
from app.composition.infrastructure_services import (
    build_filesystem_service,
    build_plex_library_destination_selector,
)
from app.composition.persistence import build_antivirus_repository
from app.composition.plex_external import (
    build_add_watchlist_item_use_case,
    build_partial_scan_library_use_case,
)
from app.composition.plex_library_paths import (
    build_refresh_plex_library_disk_stats_use_case,
    build_sync_plex_library_paths_use_case,
)
from app.composition.tmdb import build_remove_watchlist_entry_use_case, build_tmdb_watchlist_adapter
from app.application.tmdb.use_cases.add_tmdb_watchlist_item_use_case import (
    AddTmdbWatchlistItemUseCase,
)
from app.application.pipelines.watchlist.use_cases.readd_watchlist_after_failure_use_case import (
    ReaddWatchlistAfterFailureUseCase,
)
from app.composition.active_downloads import (
    build_get_active_download_by_uid_query,
    build_get_all_active_downloads_query,
    build_reconcile_active_downloads_with_deluge_use_case,
)
from app.composition.deluge import build_get_torrents_status_query
from app.domain.services.ingest_destination_resolver import IngestDestinationResolver


def build_scan_torrent_use_case(session: AsyncSession) -> ScanTorrentUseCase:
    return ScanTorrentUseCase(
        get_active_download_query=build_get_active_download_by_uid_query(session),
        filesystem_service=build_filesystem_service(),
        antivirus_provider=build_antivirus_provider(),
        antivirus_repo=build_antivirus_repository(session),
    )


def build_readd_watchlist_after_failure_use_case() -> ReaddWatchlistAfterFailureUseCase:
    return ReaddWatchlistAfterFailureUseCase(
        build_add_watchlist_item_use_case(),
        AddTmdbWatchlistItemUseCase(build_tmdb_watchlist_adapter()),
    )


def build_handle_infected_torrent_use_case(
    session: AsyncSession,
) -> HandleInfectedTorrentUseCase:
    return HandleInfectedTorrentUseCase(
        deluge_provider=build_deluge_adapter(),
        add_torrent_to_blacklist_use_case=build_add_torrent_to_blacklist_use_case(
            session
        ),
        readd_watchlist_after_failure_use_case=build_readd_watchlist_after_failure_use_case(),
        reconcile_active_downloads_use_case=build_reconcile_active_downloads_with_deluge_use_case(
            session
        ),
    )


def build_ingest_clean_torrent_use_case(
    session: AsyncSession,
) -> IngestCleanTorrentUseCase:
    return IngestCleanTorrentUseCase(
        filesystem_service=build_filesystem_service(),
        antivirus_repo=build_antivirus_repository(session),
        deluge_provider=build_deluge_adapter(),
        destination_selector=build_plex_library_destination_selector(session),
        destination_resolver=IngestDestinationResolver(),
        partial_scan_library_use_case=build_partial_scan_library_use_case(),
        sync_library_paths_use_case=build_sync_plex_library_paths_use_case(session),
        refresh_disk_stats_use_case=build_refresh_plex_library_disk_stats_use_case(session),
        reconcile_active_downloads_use_case=build_reconcile_active_downloads_with_deluge_use_case(
            session
        ),
        remove_watchlist_entry_use_case=build_remove_watchlist_entry_use_case(session),
    )


def build_scan_and_ingest_torrent_use_case(
    session: AsyncSession,
) -> ScanAndIngestTorrentUseCase:
    return ScanAndIngestTorrentUseCase(
        get_active_download_query=build_get_active_download_by_uid_query(session),
        scan_torrent_use_case=build_scan_torrent_use_case(session),
        filesystem_service=build_filesystem_service(),
        antivirus_repo=build_antivirus_repository(session),
        handle_infected_torrent_use_case=build_handle_infected_torrent_use_case(session),
        ingest_clean_torrent_use_case=build_ingest_clean_torrent_use_case(session),
    )


def build_handle_unhealthy_torrent_use_case(
    session: AsyncSession,
) -> HandleUnhealthyTorrentUseCase:
    return HandleUnhealthyTorrentUseCase(
        deluge_provider=build_deluge_adapter(),
        add_torrent_to_blacklist_use_case=build_add_torrent_to_blacklist_use_case(
            session
        ),
        readd_watchlist_after_failure_use_case=build_readd_watchlist_after_failure_use_case(),
    )


def build_process_deluge_torrents_use_case(
    session: AsyncSession,
) -> ProcessDelugeTorrentsUseCase:
    return ProcessDelugeTorrentsUseCase(
        get_torrents_status_query=build_get_torrents_status_query(),
        get_all_active_downloads_query=build_get_all_active_downloads_query(session),
        scan_and_ingest_torrent_use_case=build_scan_and_ingest_torrent_use_case(session),
        handle_unhealthy_torrent_use_case=build_handle_unhealthy_torrent_use_case(session),
        reconcile_active_downloads_use_case=build_reconcile_active_downloads_with_deluge_use_case(
            session
        ),
        refresh_disk_stats_use_case=build_refresh_plex_library_disk_stats_use_case(session),
    )
