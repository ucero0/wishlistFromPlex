"""Map persisted library path rows to disk usage DTOs."""
from app.domain.models.plex_library_disk_usage import PlexLibraryPathDiskInfo
from app.domain.models.plex_library_path import PlexLibraryPath


def path_row_to_disk_info(row: PlexLibraryPath) -> PlexLibraryPathDiskInfo:
    error = row.disk_stats_error
    if error is None and row.total_bytes is None and row.disk_stats_synced_at is None:
        error = "disk stats not yet measured"
    return PlexLibraryPathDiskInfo(
        path=row.path,
        volume_root=row.volume_root,
        total_bytes=row.total_bytes,
        used_bytes=row.used_bytes,
        free_bytes=row.free_bytes,
        used_percent=row.used_percent,
        error=error,
    )
