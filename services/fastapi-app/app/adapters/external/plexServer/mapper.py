"""Maps Plex server infrastructure responses to domain models."""
from app.domain.models.plexLibraryLocations import (
    PlexLibraryLocationsByMedia,
    PlexLibrarySectionLocation,
)
from app.infrastructure.externalApis.plex.plexServer.schemas import (
    PlexLibraryLocationsByMediaResponse,
)


def library_locations_response_to_domain(
    response: PlexLibraryLocationsByMediaResponse,
) -> PlexLibraryLocationsByMedia:
    """Convert raw Plex /library/sections aggregate to domain."""
    sections = [
        PlexLibrarySectionLocation(
            section_id=item.section_id,
            section_title=item.section_title,
            media_type=item.media_type,
            locations=item.locations,
        )
        for item in response.items
    ]
    return PlexLibraryLocationsByMedia(sections=sections)
