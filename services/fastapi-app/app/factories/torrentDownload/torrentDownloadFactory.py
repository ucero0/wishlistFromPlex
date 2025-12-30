"""Factory for TorrentDownload queries and use cases."""
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from app.infrastructure.persistence.database import get_db
from app.infrastructure.persistence.torrentDownloads.repo.torrent_repository import TorrentRepository
from app.application.torrentDownload.queries import (
    GetTorrentDownloadByIdQuery,
    GetTorrentDownloadByUidQuery,
    GetTorrentDownloadsByGuidPlexQuery,
    IsGuidPlexDownloadingQuery,
    GetTorrentDownloadByGuidProwlarrQuery,
    GetTorrentDownloadsByTypeQuery,
    GetAllTorrentDownloadsQuery,
)
from app.application.torrentDownload.useCases import (
    CreateTorrentDownloadUseCase,
    UpdateTorrentDownloadUseCase,
    DeleteTorrentDownloadUseCase,
    DeleteTorrentDownloadByIdUseCase,
)


def _get_repo(session: AsyncSession) -> TorrentRepository:
    """Helper function to create repository instance."""
    return TorrentRepository(session)


# Query Factories
def create_get_torrent_download_by_id_query(
    session: AsyncSession = Depends(get_db)
) -> GetTorrentDownloadByIdQuery:
    """Factory function to create GetTorrentDownloadByIdQuery."""
    return GetTorrentDownloadByIdQuery(_get_repo(session))


def create_get_torrent_download_by_uid_query(
    session: AsyncSession = Depends(get_db)
) -> GetTorrentDownloadByUidQuery:
    """Factory function to create GetTorrentDownloadByUidQuery."""
    return GetTorrentDownloadByUidQuery(_get_repo(session))


def create_get_torrent_downloads_by_guid_plex_query(
    session: AsyncSession = Depends(get_db)
) -> GetTorrentDownloadsByGuidPlexQuery:
    """Factory function to create GetTorrentDownloadsByGuidPlexQuery."""
    return GetTorrentDownloadsByGuidPlexQuery(_get_repo(session))


def create_is_guid_plex_downloading_query(
    session: AsyncSession = Depends(get_db)
) -> IsGuidPlexDownloadingQuery:
    """Factory function to create IsGuidPlexDownloadingQuery."""
    return IsGuidPlexDownloadingQuery(_get_repo(session))


def create_get_torrent_download_by_guid_prowlarr_query(
    session: AsyncSession = Depends(get_db)
) -> GetTorrentDownloadByGuidProwlarrQuery:
    """Factory function to create GetTorrentDownloadByGuidProwlarrQuery."""
    return GetTorrentDownloadByGuidProwlarrQuery(_get_repo(session))


def create_get_torrent_downloads_by_type_query(
    session: AsyncSession = Depends(get_db)
) -> GetTorrentDownloadsByTypeQuery:
    """Factory function to create GetTorrentDownloadsByTypeQuery."""
    return GetTorrentDownloadsByTypeQuery(_get_repo(session))


def create_get_all_torrent_downloads_query(
    session: AsyncSession = Depends(get_db)
) -> GetAllTorrentDownloadsQuery:
    """Factory function to create GetAllTorrentDownloadsQuery."""
    return GetAllTorrentDownloadsQuery(_get_repo(session))


# Use Case Factories
def create_create_torrent_download_use_case(
    session: AsyncSession = Depends(get_db)
) -> CreateTorrentDownloadUseCase:
    """Factory function to create CreateTorrentDownloadUseCase."""
    return CreateTorrentDownloadUseCase(_get_repo(session))


def create_update_torrent_download_use_case(
    session: AsyncSession = Depends(get_db)
) -> UpdateTorrentDownloadUseCase:
    """Factory function to create UpdateTorrentDownloadUseCase."""
    return UpdateTorrentDownloadUseCase(_get_repo(session))


def create_delete_torrent_download_use_case(
    session: AsyncSession = Depends(get_db)
) -> DeleteTorrentDownloadUseCase:
    """Factory function to create DeleteTorrentDownloadUseCase."""
    return DeleteTorrentDownloadUseCase(_get_repo(session))


def create_delete_torrent_download_by_id_use_case(
    session: AsyncSession = Depends(get_db)
) -> DeleteTorrentDownloadByIdUseCase:
    """Factory function to create DeleteTorrentDownloadByIdUseCase."""
    return DeleteTorrentDownloadByIdUseCase(_get_repo(session))

