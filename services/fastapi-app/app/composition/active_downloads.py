"""Composition root for torrent download queries and use cases."""
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.pipelines.watchlist.use_cases.reconcile_active_downloads_with_deluge_use_case import (
    ReconcileActiveDownloadsWithDelugeUseCase,
)
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
from app.composition.persistence import build_active_download_repository
from app.composition.deluge import build_get_torrents_status_query


def build_get_active_download_by_id_query(
    session: AsyncSession,
) -> GetActiveDownloadByIdQuery:
    return GetActiveDownloadByIdQuery(build_active_download_repository(session))


def build_get_active_download_by_uid_query(
    session: AsyncSession,
) -> GetActiveDownloadByUidQuery:
    return GetActiveDownloadByUidQuery(build_active_download_repository(session))


def build_get_active_downloads_by_guid_plex_query(
    session: AsyncSession,
) -> GetActiveDownloadsByGuidPlexQuery:
    return GetActiveDownloadsByGuidPlexQuery(build_active_download_repository(session))


def build_is_guid_plex_downloading_query(
    session: AsyncSession,
) -> IsGuidPlexDownloadingQuery:
    return IsGuidPlexDownloadingQuery(build_active_download_repository(session))


def build_get_active_download_by_guid_prowlarr_query(
    session: AsyncSession,
) -> GetActiveDownloadByGuidProwlarrQuery:
    return GetActiveDownloadByGuidProwlarrQuery(build_active_download_repository(session))


def build_get_active_downloads_by_type_query(
    session: AsyncSession,
) -> GetActiveDownloadsByTypeQuery:
    return GetActiveDownloadsByTypeQuery(build_active_download_repository(session))


def build_get_all_active_downloads_query(
    session: AsyncSession,
) -> GetAllActiveDownloadsQuery:
    return GetAllActiveDownloadsQuery(build_active_download_repository(session))


def build_create_active_download_use_case(
    session: AsyncSession,
) -> CreateActiveDownloadUseCase:
    return CreateActiveDownloadUseCase(build_active_download_repository(session))


def build_update_active_download_use_case(
    session: AsyncSession,
) -> UpdateActiveDownloadUseCase:
    return UpdateActiveDownloadUseCase(build_active_download_repository(session))


def build_delete_active_download_use_case(
    session: AsyncSession,
) -> DeleteActiveDownloadUseCase:
    return DeleteActiveDownloadUseCase(build_active_download_repository(session))


def build_delete_active_download_by_id_use_case(
    session: AsyncSession,
) -> DeleteActiveDownloadByIdUseCase:
    return DeleteActiveDownloadByIdUseCase(build_active_download_repository(session))


def build_reconcile_active_downloads_with_deluge_use_case(
    session: AsyncSession,
) -> ReconcileActiveDownloadsWithDelugeUseCase:
    return ReconcileActiveDownloadsWithDelugeUseCase(
        get_all_active_downloads_query=build_get_all_active_downloads_query(session),
        get_torrents_status_query=build_get_torrents_status_query(),
        delete_active_download_use_case=build_delete_active_download_use_case(session),
        update_active_download_use_case=build_update_active_download_use_case(session),
    )
