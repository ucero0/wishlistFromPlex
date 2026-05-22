"""Query: unique media HDD/volume devices from persisted Plex library path stats."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.domain.models.plexLibraryPath import PlexLibraryPath
from app.domain.ports.repositories.plex.plexLibraryPathRepo import PlexLibraryPathRepoPort


class PlexMediaHddDevice(BaseModel):
    """One volume root (HDD/mount) with space stats and library folders on it."""

    volume_root: str
    total_bytes: int | None = None
    used_bytes: int | None = None
    free_bytes: int | None = None
    used_percent: float | None = None
    error: str | None = None
    library_paths: list[str] = []
    last_synced_at: datetime | None = None
    disk_stats_synced_at: datetime | None = None


class PlexMediaHddDevicesResult(BaseModel):
    devices: list[PlexMediaHddDevice]
    total: int


class GetPlexLibraryMediaDevicesFromDbQuery:
    """Aggregate active DB paths by ``volume_root`` using stored disk fields."""

    def __init__(self, path_repo: PlexLibraryPathRepoPort):
        self._path_repo = path_repo

    async def execute(self, *, active_only: bool = True) -> PlexMediaHddDevicesResult:
        rows = await self._path_repo.list_all(active_only=active_only)
        by_volume: dict[str, PlexMediaHddDevice] = {}
        unknown: PlexMediaHddDevice | None = None

        for row in rows:
            key = row.volume_root
            if key:
                if key not in by_volume:
                    by_volume[key] = PlexMediaHddDevice(
                        volume_root=key,
                        total_bytes=row.total_bytes,
                        used_bytes=row.used_bytes,
                        free_bytes=row.free_bytes,
                        used_percent=row.used_percent,
                        error=row.disk_stats_error,
                    )
                device = by_volume[key]
            else:
                if unknown is None:
                    unknown = PlexMediaHddDevice(
                        volume_root="(unresolved)",
                        error=row.disk_stats_error or "volume root unknown",
                    )
                device = unknown
            self._merge_row_into_device(row, device)

        devices = sorted(by_volume.values(), key=lambda d: d.volume_root)
        if unknown and unknown.library_paths:
            devices.append(unknown)
        return PlexMediaHddDevicesResult(devices=devices, total=len(devices))

    def _merge_row_into_device(self, row: PlexLibraryPath, device: PlexMediaHddDevice) -> None:
        if row.path not in device.library_paths:
            device.library_paths.append(row.path)
        device.last_synced_at = _max_datetime(device.last_synced_at, row.last_synced_at)
        device.disk_stats_synced_at = _max_datetime(
            device.disk_stats_synced_at, row.disk_stats_synced_at
        )
        if row.total_bytes is not None:
            device.total_bytes = row.total_bytes
            device.used_bytes = row.used_bytes
            device.free_bytes = row.free_bytes
            device.used_percent = row.used_percent
            if row.disk_stats_error is None:
                device.error = None


def _max_datetime(
    a: Optional[datetime], b: Optional[datetime]
) -> Optional[datetime]:
    if a is None:
        return b
    if b is None:
        return a
    return max(a, b)
