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
    return SyncTorrentDownloadWithDelugeUseCase(
        getAllTorrentDownloadsQuery=create_get_all_torrent_downloads_query(session),
        getTorrentsStatusQuery=createGetTorrentsStatusQuery(),
        deleteTorrentDownloadUseCase=create_delete_torrent_download_use_case(session),
        updateTorrentDownloadUseCase=create_update_torrent_download_use_case(session),
    )
