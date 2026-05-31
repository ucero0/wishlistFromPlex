"""Stable keys for grouping the same movie/show across Plex and TMDB watchlists."""
from app.domain.models.media import MediaItem
from app.domain.services.tmdb_guid import parse_tmdb_guid


def media_identity_key(item: MediaItem) -> str:
    """Prefer Plex library guid so TMDB and Plex rows for the same title merge."""
    if item.plex_library_guid:
        return f"plex-lib:{item.plex_library_guid}"
    parsed = parse_tmdb_guid(item.guid or "")
    if parsed:
        media_type, tmdb_id = parsed
        return f"tmdb:{media_type}:{tmdb_id}"
    if item.guid:
        return f"guid:{item.guid}"
    media_type = item.type.value if hasattr(item.type, "value") else str(item.type)
    return f"fallback:{media_type}:{item.title}:{item.year}"
