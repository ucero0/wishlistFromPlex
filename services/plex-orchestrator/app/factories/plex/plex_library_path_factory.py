"""Factories for Plex library path sync and listing."""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.plex.queries.get_plex_library_media_devices_from_db_query import (
    GetPlexLibraryMediaDevicesFromDbQuery,
)
from app.application.plex.queries.get_plex_library_paths_disk_usage_from_db_query import (
    GetPlexLibraryPathsDiskUsageFromDbQuery,
)
from app.application.plex.queries.list_plex_library_paths_flat_query import ListPlexLibraryPathsFlatQuery
from app.application.plex.use_cases.refresh_plex_library_paths_before_serve_use_case import (
    RefreshPlexLibraryPathsBeforeServeUseCase,
)
from app.composition.infrastructure_services import build_plex_library_destination_selector
from app.composition.plex_library_paths import (
    build_get_plex_library_media_devices_from_db_query,
    build_get_plex_library_paths_disk_usage_from_db_query,
    build_list_plex_library_paths_flat_query,
    build_refresh_plex_library_paths_before_serve_use_case,
    build_sync_plex_library_paths_use_case,
)
from app.infrastructure.persistence.database import get_db


def create_sync_plex_library_paths_use_case(
    session: AsyncSession = Depends(get_db),
):
    return build_sync_plex_library_paths_use_case(session)


def create_list_plex_library_paths_flat_query(
    session: AsyncSession = Depends(get_db),
) -> ListPlexLibraryPathsFlatQuery:
    return build_list_plex_library_paths_flat_query(session)


def create_get_plex_library_paths_disk_usage_from_db_query(
    session: AsyncSession = Depends(get_db),
) -> GetPlexLibraryPathsDiskUsageFromDbQuery:
    return build_get_plex_library_paths_disk_usage_from_db_query(session)


def create_get_plex_library_media_devices_from_db_query(
    session: AsyncSession = Depends(get_db),
) -> GetPlexLibraryMediaDevicesFromDbQuery:
    return build_get_plex_library_media_devices_from_db_query(session)


def create_refresh_plex_library_paths_before_serve_use_case(
    session: AsyncSession = Depends(get_db),
) -> RefreshPlexLibraryPathsBeforeServeUseCase:
    return build_refresh_plex_library_paths_before_serve_use_case(session)


def create_plex_library_destination_selector_for_session(session: AsyncSession):
    return build_plex_library_destination_selector(session)
