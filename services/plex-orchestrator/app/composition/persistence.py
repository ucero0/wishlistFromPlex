"""Central repository construction for the composition root."""
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.persistence.antivirus.repo.antivirus_repository import (
    AntivirusRepository,
)
from app.infrastructure.persistence.blacklist_torrent.repo.blacklist_torrent_repository import (
    BlacklistActiveDownloadRepository,
)
from app.infrastructure.persistence.deferred_downloads.repo.deferred_download_repository import (
    DeferredDownloadRepository,
)
from app.infrastructure.persistence.plex.repo.plex_library_path_repository import (
    PlexLibraryPathRepository,
)
from app.infrastructure.persistence.plex.repo.plex_user_repository import PlexUserRepository
from app.infrastructure.persistence.tmdb.repo.tmdb_user_repository import TmdbUserRepository
from app.infrastructure.persistence.plex.repo.plex_server_config_repository import (
    PlexServerConfigRepository,
)
from app.infrastructure.persistence.active_downloads.repo.active_download_repository import (
    ActiveDownloadRepository,
)


def build_active_download_repository(session: AsyncSession) -> ActiveDownloadRepository:
    return ActiveDownloadRepository(session)


def build_antivirus_repository(session: AsyncSession) -> AntivirusRepository:
    return AntivirusRepository(session)


def build_blacklist_torrent_repository(session: AsyncSession) -> BlacklistActiveDownloadRepository:
    return BlacklistActiveDownloadRepository(session)


def build_deferred_download_repository(session: AsyncSession) -> DeferredDownloadRepository:
    return DeferredDownloadRepository(session)


def build_plex_user_repository(session: AsyncSession) -> PlexUserRepository:
    return PlexUserRepository(session)


def build_tmdb_user_repository(session: AsyncSession) -> TmdbUserRepository:
    return TmdbUserRepository(session)


def build_plex_library_path_repository(session: AsyncSession) -> PlexLibraryPathRepository:
    return PlexLibraryPathRepository(session)


def build_plex_server_config_repository(session: AsyncSession) -> PlexServerConfigRepository:
    return PlexServerConfigRepository(session)

