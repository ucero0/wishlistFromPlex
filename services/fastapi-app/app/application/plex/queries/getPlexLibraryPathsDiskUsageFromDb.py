"""Query: disk usage for Plex library paths from persisted DB stats."""
from app.application.plex.mappers.plex_library_path_disk_mapper import path_row_to_disk_info
from app.application.plex.mappers.plex_library_path_mapper import (
    paths_to_locations_by_media,
)
from app.domain.models.plexLibraryDiskUsage import (
    PlexLibraryLocationsDiskUsage,
    PlexLibrarySectionDiskUsage,
)
from app.domain.ports.repositories.plex.plexLibraryPathRepo import PlexLibraryPathRepoPort


class GetPlexLibraryPathsDiskUsageFromDbQuery:
    """Library sections with per-path stats stored in ``plex_library_paths``."""

    def __init__(self, path_repo: PlexLibraryPathRepoPort):
        self._path_repo = path_repo

    async def execute(self, *, active_only: bool = True) -> PlexLibraryLocationsDiskUsage:
        rows = await self._path_repo.list_all(active_only=active_only)
        layout = paths_to_locations_by_media(rows)
        by_path = {r.path: r for r in rows}
        sections: list[PlexLibrarySectionDiskUsage] = []
        for sec in layout.sections:
            locations = [
                path_row_to_disk_info(by_path[p])
                for p in sec.locations
                if p in by_path
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
