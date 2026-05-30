"""Map Plex library location models to persisted path rows."""
from datetime import datetime, timezone

from app.domain.models.plex_library_locations import PlexLibraryLocationsByMedia
from app.domain.models.plex_library_path import PlexLibraryPath


def locations_by_media_to_paths(
    layout: PlexLibraryLocationsByMedia,
    *,
    synced_at: datetime | None = None,
) -> list[PlexLibraryPath]:
    """Flatten section locations into DB rows (one row per root path)."""
    when = synced_at or datetime.now(timezone.utc)
    paths: list[PlexLibraryPath] = []
    for section in layout.sections:
        for loc_path in section.locations:
            paths.append(
                PlexLibraryPath(
                    section_id=section.section_id,
                    section_title=section.section_title,
                    media_type=section.media_type,
                    path=loc_path,
                    is_active=True,
                    last_synced_at=when,
                )
            )
    return paths


def paths_to_locations_by_media(paths: list[PlexLibraryPath]) -> PlexLibraryLocationsByMedia:
    """Rebuild section layout from DB rows (same shape as Plex API query)."""
    from app.domain.models.plex_library_locations import PlexLibrarySectionLocation

    by_section: dict[str, PlexLibrarySectionLocation] = {}
    for row in paths:
        if row.section_id not in by_section:
            by_section[row.section_id] = PlexLibrarySectionLocation(
                section_id=row.section_id,
                section_title=row.section_title,
                media_type=row.media_type,
                locations=[],
            )
        if row.path not in by_section[row.section_id].locations:
            by_section[row.section_id].locations.append(row.path)
    return PlexLibraryLocationsByMedia(sections=list(by_section.values()))
