"""Factory for ActiveDownload queries and use cases."""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.active_downloads.queries import (
    GetAllActiveDownloadsQuery,
    GetActiveDownloadByGuidProwlarrQuery,
    GetActiveDownloadByIdQuery,
    GetActiveDownloadByUidQuery,
    GetActiveDownloadsByGuidPlexQuery,
    GetActiveDownloadsByTypeQuery,
    IsGuidPlexDownloadingQuery,
)
from app.application.active_downloads.use_cases import (
    CreateActiveDownloadUseCase,
    DeleteActiveDownloadByIdUseCase,
    DeleteActiveDownloadUseCase,
    UpdateActiveDownloadUseCase,
)
from app.composition.active_downloads import (
    build_create_active_download_use_case,
    build_delete_active_download_by_id_use_case,
    build_delete_active_download_use_case,
    build_get_all_active_downloads_query,
    build_get_active_download_by_guid_prowlarr_query,
    build_get_active_download_by_id_query,
    build_get_active_download_by_uid_query,
    build_get_active_downloads_by_guid_plex_query,
    build_get_active_downloads_by_type_query,
    build_is_guid_plex_downloading_query,
    build_update_active_download_use_case,
)
from app.infrastructure.persistence.database import get_db


def create_get_active_download_by_id_query(
    session: AsyncSession = Depends(get_db),
) -> GetActiveDownloadByIdQuery:
    return build_get_active_download_by_id_query(session)


def create_get_active_download_by_uid_query(
    session: AsyncSession = Depends(get_db),
) -> GetActiveDownloadByUidQuery:
    return build_get_active_download_by_uid_query(session)


def create_get_active_downloads_by_guid_plex_query(
    session: AsyncSession = Depends(get_db),
) -> GetActiveDownloadsByGuidPlexQuery:
    return build_get_active_downloads_by_guid_plex_query(session)


def create_is_guid_plex_downloading_query(
    session: AsyncSession = Depends(get_db),
) -> IsGuidPlexDownloadingQuery:
    return build_is_guid_plex_downloading_query(session)


def create_get_active_download_by_guid_prowlarr_query(
    session: AsyncSession = Depends(get_db),
) -> GetActiveDownloadByGuidProwlarrQuery:
    return build_get_active_download_by_guid_prowlarr_query(session)


def create_get_active_downloads_by_type_query(
    session: AsyncSession = Depends(get_db),
) -> GetActiveDownloadsByTypeQuery:
    return build_get_active_downloads_by_type_query(session)


def create_get_all_active_downloads_query(
    session: AsyncSession = Depends(get_db),
) -> GetAllActiveDownloadsQuery:
    return build_get_all_active_downloads_query(session)


def create_create_active_download_use_case(
    session: AsyncSession = Depends(get_db),
) -> CreateActiveDownloadUseCase:
    return build_create_active_download_use_case(session)


def create_update_active_download_use_case(
    session: AsyncSession = Depends(get_db),
) -> UpdateActiveDownloadUseCase:
    return build_update_active_download_use_case(session)


def create_delete_active_download_use_case(
    session: AsyncSession = Depends(get_db),
) -> DeleteActiveDownloadUseCase:
    return build_delete_active_download_use_case(session)


def create_delete_active_download_by_id_use_case(
    session: AsyncSession = Depends(get_db),
) -> DeleteActiveDownloadByIdUseCase:
    return build_delete_active_download_by_id_use_case(session)
