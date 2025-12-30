from app.application.orchestrators.useCases.downloadWatchListMedia import DownloadWatchListMediaUseCase
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from app.infrastructure.persistence.database import get_db
from app.factories.plex.plexWatchListFactory import createGetWatchListQuery, createRemoveWatchListItemUseCase
from app.factories.plex.plexUsersFactory import createGetPlexUserQuery
from app.factories.plex.plexServerFactory import createIsItemInLibraryQuery
from app.factories.deluge.delugeFactory import createGetTorrentByNameQuery
from app.factories.prowlarr.prowlarrFactory import createDownloadTorrentUseCase, createFindBestTorrentQuery
from app.factories.antivirus.antivirusFactory import create_check_infected_by_guid_prowlarr_query
from app.factories.torrentDownload.torrentDownloadFactory import create_create_torrent_download_use_case, create_is_guid_plex_downloading_query
from app.factories.orchestrators.syncTorrentDownloadWithDelugeFactory import create_sync_torrent_download_with_deluge_use_case
from app.factories.tmdb.tmdbFactory import create_get_original_title_from_tmdb_query
def create_download_watch_list_media_use_case(
    session: AsyncSession = Depends(get_db)
) -> DownloadWatchListMediaUseCase:
    """Factory function to create DownloadWatchListMediaUseCase with all dependencies."""
    # Create GetPlexUserQuery with database session
    get_plex_user_query = createGetPlexUserQuery(session)
    get_watch_list_query = createGetWatchListQuery()
    is_item_in_library_query = createIsItemInLibraryQuery()
    get_torrent_by_name_query = createGetTorrentByNameQuery()
    remove_watch_list_item_use_case = createRemoveWatchListItemUseCase()
    download_torrent_use_case = createDownloadTorrentUseCase()
    find_best_torrent_query = createFindBestTorrentQuery()
    
    # Use async session for async repositories
    check_infected_by_guid_prowlarr_query = create_check_infected_by_guid_prowlarr_query(session)
    create_torrent_download_use_case = create_create_torrent_download_use_case(session)
    is_guid_plex_downloading_query = create_is_guid_plex_downloading_query(session)
    sync_torrent_download_with_deluge_use_case = create_sync_torrent_download_with_deluge_use_case(session)
    get_original_title_from_tmdb_query = create_get_original_title_from_tmdb_query()
    # Create DownloadWatchListMediaUseCase with all dependencies
    return DownloadWatchListMediaUseCase(
        getPlexUserQuery=get_plex_user_query,
        getWatchListQuery=get_watch_list_query,
        isItemInLibraryQuery=is_item_in_library_query,
        getTorrentByNameQuery=get_torrent_by_name_query,
        removeWatchListItemUseCase=remove_watch_list_item_use_case,
        downloadTorrentUseCase=download_torrent_use_case,
        findBestTorrentQuery=find_best_torrent_query,
        checkInfectedByGuidProwlarrQuery=check_infected_by_guid_prowlarr_query,
        createTorrentDownloadUseCase=create_torrent_download_use_case,
        isGuidPlexDownloadingQuery=is_guid_plex_downloading_query,
        syncTorrentDownloadWithDelugeUseCase=sync_torrent_download_with_deluge_use_case,
        getOriginalTitleFromTMDBQuery=get_original_title_from_tmdb_query,
    )

