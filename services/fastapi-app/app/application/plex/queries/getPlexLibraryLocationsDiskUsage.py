"""Query: Plex library paths plus volume root and disk usage from this host."""
from app.application.plex.helpers.plex_disk_usage import build_disk_info_for_path
from app.domain.models.plexLibraryDiskUsage import (
    PlexLibraryLocationsDiskUsage,
    PlexLibrarySectionDiskUsage,
)
from app.domain.services.filesystem_service import FilesystemService
from app.domain.ports.external.plex.plexServerLibraryProvider import PlexServerLibraryProvider


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
            locations = [
                build_disk_info_for_path(p, self._filesystem) for p in sec.locations
            ]
            sections.append(
                PlexLibrarySectionDiskUsage(
                    section_id=sec.section_id,
                    section_title=sec.section_title,
                    media_type=sec.media_type,
                    locations=locations,
                )
            )
        return PlexLibraryLocationsDiskUsage(sections=sections)
