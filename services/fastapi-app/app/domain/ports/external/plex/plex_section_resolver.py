"""Port for resolving Plex library section ID by media type."""
from typing import Optional, Protocol


class PlexSectionResolverPort(Protocol):
    """Resolves Plex library section ID for a given media type (movie/show)."""

    def get_section_id_for_media_type(self, media_type: str) -> Optional[int]:
        """
        Return the Plex library section ID for the given media type.

        Args:
            media_type: Domain media type (e.g. "movie", "show", "tvshow").

        Returns:
            Section ID if known, None otherwise.
        """
        ...
