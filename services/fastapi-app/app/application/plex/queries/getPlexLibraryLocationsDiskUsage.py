"""Query: Plex library paths plus volume root and disk usage from this host."""
import logging

from app.domain.models.plexLibraryDiskUsage import (
    PlexLibraryLocationsDiskUsage,
    PlexLibraryPathDiskInfo,
    PlexLibrarySectionDiskUsage,
)
from app.domain.services.filesystem_service import FilesystemService
from app.domain.ports.external.plex.plexServerLibraryProvider import PlexServerLibraryProvider

logger = logging.getLogger(__name__)


class GetPlexLibraryLocationsDiskUsageQuery:
    """Combines Plex Server library paths with local volume and ``shutil.disk_usage`` stats."""

    def __init__(
        self,
        library_provider: PlexServerLibraryProvider,
        filesystem: FilesystemService,
    ):
        self._library = library_provider
        self._filesystem = filesystem

    async def execute(self, user_token: str) -> PlexLibraryLocationsDiskUsage:
        layout = await self._library.get_library_locations_by_media(user_token)
        sections: list[PlexLibrarySectionDiskUsage] = []
        for sec in layout.sections:
            locations = [self._disk_info_for_path(p) for p in sec.locations]
            sections.append(
                PlexLibrarySectionDiskUsage(
                    section_id=sec.section_id,
                    section_title=sec.section_title,
                    media_type=sec.media_type,
                    locations=locations,
                )
            )
        return PlexLibraryLocationsDiskUsage(sections=sections)

    def _disk_info_for_path(self, loc_path: str) -> PlexLibraryPathDiskInfo:
        try:
            volume_root = self._filesystem.get_volume_root(loc_path)
            usage = self._filesystem.get_disk_usage(loc_path)
            return PlexLibraryPathDiskInfo(
                path=loc_path,
                volume_root=volume_root,
                total_bytes=usage.total_bytes,
                used_bytes=usage.used_bytes,
                free_bytes=usage.free_bytes,
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
                error=str(exc),
            )
