"""Factories for Plex library path sync and listing."""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.plex.queries.getPlexLibraryMediaDevicesFromDb import (
    GetPlexLibraryMediaDevicesFromDbQuery,
)
from app.application.plex.queries.getPlexLibraryPathsDiskUsageFromDb import (
    GetPlexLibraryPathsDiskUsageFromDbQuery,
)
from app.application.plex.queries.listPlexLibraryPaths import ListPlexLibraryPathsFromDbQuery
from app.application.plex.queries.listPlexLibraryPathsFlat import ListPlexLibraryPathsFlatQuery
from app.application.plex.useCases.refreshPlexLibraryPathsBeforeServe import (
    RefreshPlexLibraryPathsBeforeServeUseCase,
)
from app.composition.plex_library_paths import (
    build_refresh_plex_library_paths_before_serve_use_case,
    build_sync_plex_library_paths_use_case,
)
from app.domain.services.plex_library_destination_selector import (
    PlexLibraryDestinationSelector,
)
from app.infrastructure.persistence.database import get_db
from app.infrastructure.persistence.plex.repo.plexLibraryPathRepo import (
    PlexLibraryPathRepository,
)

def create_sync_plex_library_paths_use_case(
    session: AsyncSession = Depends(get_db),
):
    return build_sync_plex_library_paths_use_case(session)


def create_list_plex_library_paths_from_db_query(
    session: AsyncSession = Depends(get_db),
) -> ListPlexLibraryPathsFromDbQuery:
    return ListPlexLibraryPathsFromDbQuery(PlexLibraryPathRepository(session))


def create_list_plex_library_paths_flat_query(
    session: AsyncSession = Depends(get_db),
) -> ListPlexLibraryPathsFlatQuery:
    return ListPlexLibraryPathsFlatQuery(PlexLibraryPathRepository(session))


def create_get_plex_library_paths_disk_usage_from_db_query(
    session: AsyncSession = Depends(get_db),
) -> GetPlexLibraryPathsDiskUsageFromDbQuery:
    return GetPlexLibraryPathsDiskUsageFromDbQuery(PlexLibraryPathRepository(session))


def create_get_plex_library_media_devices_from_db_query(
    session: AsyncSession = Depends(get_db),
) -> GetPlexLibraryMediaDevicesFromDbQuery:
    return GetPlexLibraryMediaDevicesFromDbQuery(PlexLibraryPathRepository(session))


def create_refresh_plex_library_paths_before_serve_use_case(
    session: AsyncSession = Depends(get_db),
) -> RefreshPlexLibraryPathsBeforeServeUseCase:
    return build_refresh_plex_library_paths_before_serve_use_case(session)


def create_plex_library_destination_selector_for_session(
    session: AsyncSession,
) -> PlexLibraryDestinationSelector:
    from app.composition.infrastructure_services import build_filesystem_service

    return PlexLibraryDestinationSelector(
        PlexLibraryPathRepository(session),
        build_filesystem_service(),
    )

