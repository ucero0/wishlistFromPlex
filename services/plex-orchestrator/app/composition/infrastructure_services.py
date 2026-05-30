"""Shared infrastructure wiring (filesystem, download volume checks)."""
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.domain.services.download_volume_space_checker import DownloadVolumeSpaceChecker
from app.domain.services.plex_library_destination_selector import (
    PlexLibraryDestinationSelector,
)
from app.composition.persistence import build_plex_library_path_repository
from app.infrastructure.services.filesystem_service_impl import FilesystemServiceImpl


def _gb_to_bytes(gb: float) -> int:
    return int(gb * 1024**3)


def build_filesystem_service() -> FilesystemServiceImpl:
    return FilesystemServiceImpl(
        quarantine_path=settings.container_deluge_quarantine_path,
        host_fs_prefix=settings.container_host_fs_prefix,
    )


def build_download_volume_space_checker() -> DownloadVolumeSpaceChecker:
    filesystem = build_filesystem_service()
    return DownloadVolumeSpaceChecker(
        filesystem,
        settings.container_deluge_quarantine_path,
        min_free_buffer_bytes=_gb_to_bytes(settings.download_min_free_buffer_gb),
        default_required_bytes_when_unknown=_gb_to_bytes(
            settings.download_default_required_gb
        ),
    )


def build_plex_library_destination_selector(
    session: AsyncSession,
) -> PlexLibraryDestinationSelector:
    return PlexLibraryDestinationSelector(
        build_plex_library_path_repository(session),
        build_filesystem_service(),
        disk_stats_max_age_hours=settings.plex_library_disk_stats_max_age_hours,
    )
