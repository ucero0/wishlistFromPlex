"""Composition root helpers for Plex library path sync."""
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.plex.useCases.syncPlexLibraryPaths import (
    SyncPlexLibraryPathsFromServerUseCase,
)
from app.application.plex.useCases.syncPlexLibraryPathsForActiveUsers import (
    SyncPlexLibraryPathsForActiveUsersUseCase,
)
from app.application.plex.useCases.refreshPlexLibraryPathsBeforeServe import (
    RefreshPlexLibraryPathsBeforeServeUseCase,
)
from app.composition.infrastructure_services import build_filesystem_service
from app.factories.plex.plexServerFactory import createGetPlexLibraryLocationsByMediaQuery
from app.infrastructure.persistence.plex.repo.plexLibraryPathRepo import (
    PlexLibraryPathRepository,
)
from app.infrastructure.persistence.plex.repo.plexUserRepo import PlexUserRepo


def build_sync_plex_library_paths_use_case(
    session: AsyncSession,
) -> SyncPlexLibraryPathsFromServerUseCase:
    return SyncPlexLibraryPathsFromServerUseCase(
        createGetPlexLibraryLocationsByMediaQuery(),
        PlexLibraryPathRepository(session),
        build_filesystem_service(),
    )


def build_refresh_plex_library_paths_before_serve_use_case(
    session: AsyncSession,
) -> RefreshPlexLibraryPathsBeforeServeUseCase:
    path_repo = PlexLibraryPathRepository(session)
    return RefreshPlexLibraryPathsBeforeServeUseCase(
        path_repo,
        PlexUserRepo(session),
        build_sync_plex_library_paths_use_case(session),
        build_filesystem_service(),
    )


def build_sync_plex_library_paths_for_active_users_use_case(
    session: AsyncSession,
) -> SyncPlexLibraryPathsForActiveUsersUseCase:
    return SyncPlexLibraryPathsForActiveUsersUseCase(
        PlexUserRepo(session),
        build_sync_plex_library_paths_use_case(session),
    )
