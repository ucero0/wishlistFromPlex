"""Map domain disk stats to HTTP bodies with human-readable sizes."""
from typing import Iterable, List

from app.adapters.http.mappers.disk_size_format import format_bytes_for_display
from app.adapters.http.schemas.plex.plexLibraryPathSchemas import (
    PlexLibraryPathDiskInfoBody,
    PlexLibraryPathItem,
    PlexLibrarySectionDiskUsageBody,
    PlexLibraryServeMetaBody,
    PlexMediaHddDeviceBody,
)
from app.application.plex.queries.getPlexLibraryMediaDevicesFromDb import PlexMediaHddDevice
from app.application.plex.useCases.refreshPlexLibraryPathsBeforeServe import (
    PlexLibraryRefreshMeta,
)
from app.domain.models.plexLibraryDiskUsage import (
    PlexLibraryPathDiskInfo,
    PlexLibrarySectionDiskUsage,
)
from app.domain.models.plexLibraryPath import PlexLibraryPath


def path_row_to_http_item(row: PlexLibraryPath) -> PlexLibraryPathItem:
    return PlexLibraryPathItem(
        id=row.id or 0,
        section_id=row.section_id,
        section_title=row.section_title,
        media_type=row.media_type,
        path=row.path,
        is_active=row.is_active,
        last_synced_at=row.last_synced_at,
        volume_root=row.volume_root,
        total=format_bytes_for_display(row.total_bytes),
        used=format_bytes_for_display(row.used_bytes),
        free=format_bytes_for_display(row.free_bytes),
        used_percent=row.used_percent,
        disk_stats_synced_at=row.disk_stats_synced_at,
        disk_stats_error=row.disk_stats_error,
    )


def disk_info_to_http_body(info: PlexLibraryPathDiskInfo) -> PlexLibraryPathDiskInfoBody:
    return PlexLibraryPathDiskInfoBody(
        path=info.path,
        volume_root=info.volume_root,
        total=format_bytes_for_display(info.total_bytes),
        used=format_bytes_for_display(info.used_bytes),
        free=format_bytes_for_display(info.free_bytes),
        used_percent=info.used_percent,
        error=info.error,
    )


def media_device_to_http_body(device: PlexMediaHddDevice) -> PlexMediaHddDeviceBody:
    return PlexMediaHddDeviceBody(
        volume_root=device.volume_root,
        total=format_bytes_for_display(device.total_bytes),
        used=format_bytes_for_display(device.used_bytes),
        free=format_bytes_for_display(device.free_bytes),
        used_percent=device.used_percent,
        error=device.error,
        library_paths=device.library_paths,
        last_synced_at=device.last_synced_at,
        disk_stats_synced_at=device.disk_stats_synced_at,
    )


def section_disk_usage_to_http_body(
    section: PlexLibrarySectionDiskUsage,
) -> PlexLibrarySectionDiskUsageBody:
    return PlexLibrarySectionDiskUsageBody(
        section_id=section.section_id,
        section_title=section.section_title,
        media_type=section.media_type,
        locations=[disk_info_to_http_body(loc) for loc in section.locations],
    )


def sections_disk_usage_to_http_bodies(
    sections: Iterable[PlexLibrarySectionDiskUsage],
) -> List[PlexLibrarySectionDiskUsageBody]:
    return [section_disk_usage_to_http_body(s) for s in sections]


def refresh_meta_to_serve_body(meta: PlexLibraryRefreshMeta) -> PlexLibraryServeMetaBody:
    return PlexLibraryServeMetaBody.model_validate(meta.model_dump())
