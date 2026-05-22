"""Measure disk usage for persisted Plex paths and write stats to the database."""
from datetime import datetime, timezone

from app.application.plex.helpers.plex_disk_usage import (
    build_disk_info_for_path,
    compute_used_percent,
)
from app.domain.models.plexLibraryPath import PlexLibraryPath
from app.domain.ports.repositories.plex.plexLibraryPathRepo import PlexLibraryPathRepoPort
from app.domain.services.filesystem_service import FilesystemService


async def refresh_disk_stats_in_database(
    path_repo: PlexLibraryPathRepoPort,
    filesystem: FilesystemService,
    *,
    active_only: bool = True,
) -> datetime:
    """
    Probe each library path on this host and persist stats on success.

    On probe failure, existing DB values are kept (only ``disk_stats_error`` updated).
    """
    rows = await path_repo.list_all(active_only=active_only)
    to_persist: list[PlexLibraryPath] = []

    for row in rows:
        info = build_disk_info_for_path(row.path, filesystem)
        if info.error:
            to_persist.append(
                row.model_copy(
                    update={
                        "volume_root": info.volume_root or row.volume_root,
                        "disk_stats_error": info.error,
                    }
                )
            )
            continue
        used_percent = info.used_percent or compute_used_percent(
            info.used_bytes, info.total_bytes
        )
        to_persist.append(
            row.model_copy(
                update={
                    "volume_root": info.volume_root,
                    "total_bytes": info.total_bytes,
                    "used_bytes": info.used_bytes,
                    "free_bytes": info.free_bytes,
                    "used_percent": used_percent,
                    "disk_stats_error": None,
                }
            )
        )

    await path_repo.apply_disk_stats(to_persist)
    return datetime.now(timezone.utc)
