"""Composition root helpers for Plex library path sync."""
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.plex.queries.get_plex_library_media_devices_from_db_query import (
    GetPlexLibraryMediaDevicesFromDbQuery,
)
from app.application.plex.queries.get_plex_library_paths_disk_usage_from_db_query import (
    GetPlexLibraryPathsDiskUsageFromDbQuery,
)
from app.application.plex.queries.list_plex_library_paths_flat_query import ListPlexLibraryPathsFlatQuery
from app.application.plex.use_cases.refresh_plex_library_disk_stats_use_case import (
    RefreshPlexLibraryDiskStatsUseCase,
)
from app.application.plex.use_cases.refresh_plex_library_paths_before_serve_use_case import (
    RefreshPlexLibraryPathsBeforeServeUseCase,
)
from app.application.plex.use_cases.sync_plex_library_paths_use_case import (
    SyncPlexLibraryPathsFromServerUseCase,
)
from app.application.plex.use_cases.sync_plex_library_paths_for_active_users_use_case import (
    SyncPlexLibraryPathsForActiveUsersUseCase,
)
from app.composition.infrastructure_services import build_filesystem_service
from app.composition.plex_external import build_get_plex_library_locations_by_media_query
from app.composition.persistence import (
    build_plex_library_path_repository,
)


def build_list_plex_library_paths_flat_query(
    session: AsyncSession,
) -> ListPlexLibraryPathsFlatQuery:
    return ListPlexLibraryPathsFlatQuery(build_plex_library_path_repository(session))


def build_get_plex_library_paths_disk_usage_from_db_query(
    session: AsyncSession,
) -> GetPlexLibraryPathsDiskUsageFromDbQuery:
    return GetPlexLibraryPathsDiskUsageFromDbQuery(
        build_plex_library_path_repository(session)
    )


def build_get_plex_library_media_devices_from_db_query(
    session: AsyncSession,
) -> GetPlexLibraryMediaDevicesFromDbQuery:
    return GetPlexLibraryMediaDevicesFromDbQuery(
        build_plex_library_path_repository(session)
    )


def build_refresh_plex_library_disk_stats_use_case(
    session: AsyncSession,
) -> RefreshPlexLibraryDiskStatsUseCase:
    return RefreshPlexLibraryDiskStatsUseCase(
        build_plex_library_path_repository(session),
        build_filesystem_service(),
    )


def build_sync_plex_library_paths_use_case(
    session: AsyncSession,
) -> SyncPlexLibraryPathsFromServerUseCase:
    return SyncPlexLibraryPathsFromServerUseCase(
        build_get_plex_library_locations_by_media_query(),
        build_plex_library_path_repository(session),
        build_filesystem_service(),
    )


def build_refresh_plex_library_paths_before_serve_use_case(
    session: AsyncSession,
) -> RefreshPlexLibraryPathsBeforeServeUseCase:
    path_repo = build_plex_library_path_repository(session)
    return RefreshPlexLibraryPathsBeforeServeUseCase(
        path_repo,
        build_sync_plex_library_paths_use_case(session),
        build_filesystem_service(),
    )


def build_sync_plex_library_paths_for_active_users_use_case(
    session: AsyncSession,
) -> SyncPlexLibraryPathsForActiveUsersUseCase:
    return SyncPlexLibraryPathsForActiveUsersUseCase(
        build_sync_plex_library_paths_use_case(session),
    )
