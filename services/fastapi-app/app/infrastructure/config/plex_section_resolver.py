"""Adapter that resolves Plex section IDs from application settings."""
from typing import Optional

from app.core.config import settings
from app.domain.ports.external.plex.plex_section_resolver import PlexSectionResolverPort


class PlexSectionResolverAdapter(PlexSectionResolverPort):
    """Resolves Plex library section ID from settings (movies/tv shows)."""

    def get_section_id_for_media_type(self, media_type: str) -> Optional[int]:
        normalized = media_type.lower()
        if normalized == "movie":
            return settings.plex_movies_section_id
        if normalized in ("show", "tvshow"):
            return settings.plex_tvshows_section_id
        return None
