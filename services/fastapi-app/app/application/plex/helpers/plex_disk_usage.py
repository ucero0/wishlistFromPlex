"""Shared disk-usage enrichment for Plex library folder paths."""
import logging

from app.domain.models.plex_library_disk_usage import PlexLibraryPathDiskInfo
from app.domain.services.filesystem_service import FilesystemService

logger = logging.getLogger(__name__)


def compute_used_percent(
    used_bytes: int | None, total_bytes: int | None
) -> float | None:
    if (
        used_bytes is not None
        and total_bytes is not None
        and total_bytes > 0
    ):
        return round(used_bytes / total_bytes * 100.0, 2)
    return None


def build_disk_info_for_path(
    loc_path: str, filesystem: FilesystemService
) -> PlexLibraryPathDiskInfo:
    """Resolve volume root and space for one library path on this host."""
    try:
        volume_root = filesystem.get_volume_root(loc_path)
        usage = filesystem.get_disk_usage(loc_path)
        used = usage.used_bytes
        total = usage.total_bytes
        return PlexLibraryPathDiskInfo(
            path=loc_path,
            volume_root=volume_root,
            total_bytes=total,
            used_bytes=used,
            free_bytes=usage.free_bytes,
            used_percent=compute_used_percent(used, total),
            error=None,
        )
    except (ValueError, OSError) as exc:
        logger.warning(
            "Could not resolve disk usage for Plex path %r: %s",
            loc_path,
            exc,
        )
        return PlexLibraryPathDiskInfo(
            path=loc_path,
            volume_root=None,
            total_bytes=None,
            used_bytes=None,
            free_bytes=None,
            used_percent=None,
            error=str(exc),
        )
