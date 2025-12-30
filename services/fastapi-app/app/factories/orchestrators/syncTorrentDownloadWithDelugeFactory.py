"""Factory for SyncTorrentDownloadWithDelugeUseCase."""
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from app.infrastructure.persistence.database import get_db
from app.application.orchestrators.useCases.syncTorrentDownloadWithDeluge import SyncTorrentDownloadWithDelugeUseCase
from app.factories.torrentDownload.torrentDownloadFactory import (
    create_get_all_torrent_downloads_query,
    create_delete_torrent_download_use_case,
    create_update_torrent_download_use_case
)
from app.factories.deluge.delugeFactory import createGetTorrentsStatusQuery


def create_sync_torrent_download_with_deluge_use_case(
    session: AsyncSession = Depends(get_db)
) -> SyncTorrentDownloadWithDelugeUseCase:
    """Factory function to create SyncTorrentDownloadWithDelugeUseCase with all dependencies."""
    get_all_torrent_downloads_query = create_get_all_torrent_downloads_query(session)
    get_torrents_status_query = createGetTorrentsStatusQuery()
    delete_torrent_download_use_case = create_delete_torrent_download_use_case(session)
    update_torrent_download_use_case = create_update_torrent_download_use_case(session)
    
    return SyncTorrentDownloadWithDelugeUseCase(
        getAllTorrentDownloadsQuery=get_all_torrent_downloads_query,
        getTorrentsStatusQuery=get_torrents_status_query,
        deleteTorrentDownloadUseCase=delete_torrent_download_use_case,
        updateTorrentDownloadUseCase=update_torrent_download_use_case
    )

