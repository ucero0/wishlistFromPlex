"""Framework-agnostic composition helpers for orchestrators."""
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.orchestrators.useCases.downloadWatchListMedia import DownloadWatchListMediaUseCase
from app.application.orchestrators.queries.isMediaAlreadyQueuedForDownload import (
    IsMediaAlreadyQueuedForDownloadQuery,
)
from app.composition.deferred_torrent_downloads import (
    build_enqueue_deferred_torrent_download_use_case,
    build_process_deferred_torrent_downloads_use_case,
    build_send_torrent_to_deluge_service,
)
from app.composition.infrastructure_services import build_download_volume_space_checker
from app.factories.blacklist_torrent import create_is_blacklisted_by_guid_prowlarr_query
from app.factories.deluge.delugeFactory import createGetTorrentByNameQuery
from app.factories.orchestrators.syncTorrentDownloadWithDelugeFactory import (
    create_sync_torrent_download_with_deluge_use_case,
)
from app.factories.plex.plexServerFactory import createIsItemInLibraryQuery
from app.factories.plex.plexUsersFactory import createGetPlexUserQuery
from app.factories.plex.plexWatchListFactory import (
    createGetWatchListQuery,
    createRemoveWatchListItemUseCase,
)
from app.factories.prowlarr.prowlarrFactory import createFindBestTorrentQuery
from app.factories.tmdb.tmdbFactory import create_get_original_title_from_tmdb_query
from app.factories.torrentDownload.torrentDownloadFactory import (
    create_create_torrent_download_use_case,
)
from app.infrastructure.persistence.deferredTorrent.repo.deferredTorrentRepo import (
    DeferredTorrentRepository,
)
from app.infrastructure.persistence.torrentDownloads.repo.torrent_repository import (
    TorrentRepository,
)


def build_download_watch_list_media_use_case(session: AsyncSession) -> DownloadWatchListMediaUseCase:
    """Build orchestrator use case without depending on HTTP DI wrappers."""
    return DownloadWatchListMediaUseCase(
        getPlexUserQuery=createGetPlexUserQuery(session),
        getWatchListQuery=createGetWatchListQuery(),
        findBestTorrentQuery=createFindBestTorrentQuery(),
        isItemInLibraryQuery=createIsItemInLibraryQuery(),
        getTorrentByNameQuery=createGetTorrentByNameQuery(),
        removeWatchListItemUseCase=createRemoveWatchListItemUseCase(),
        is_blacklisted_by_guid_prowlarr_query=create_is_blacklisted_by_guid_prowlarr_query(
            session
        ),
        createTorrentDownloadUseCase=create_create_torrent_download_use_case(session),
        syncTorrentDownloadWithDelugeUseCase=create_sync_torrent_download_with_deluge_use_case(
            session
        ),
        getOriginalTitleFromTMDBQuery=create_get_original_title_from_tmdb_query(),
        enqueueDeferredTorrentDownloadUseCase=build_enqueue_deferred_torrent_download_use_case(
            session
        ),
        isMediaAlreadyQueuedForDownloadQuery=IsMediaAlreadyQueuedForDownloadQuery(
            TorrentRepository(session),
            DeferredTorrentRepository(session),
        ),
        downloadVolumeSpaceChecker=build_download_volume_space_checker(),
        processDeferredTorrentDownloadsUseCase=build_process_deferred_torrent_downloads_use_case(
            session
        ),
        sendTorrentToDelugeService=build_send_torrent_to_deluge_service(),
    )
