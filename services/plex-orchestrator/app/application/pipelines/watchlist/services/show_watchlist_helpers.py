"""Resolve Plex Discover rating key from a watchlist media item."""
from app.domain.models.media import MediaItem
from app.domain.services.media_library_guid import library_guid_for_media


def discover_rating_key_for_show(watchlist: MediaItem) -> str | None:
    """Plex Discover rating key — only for Plex-sourced watchlist shows."""
    guid = watchlist.guid or ""
    prefix = "plex://show/"
    if guid.startswith(prefix):
        if watchlist.rating_key:
            return watchlist.rating_key
        return guid[len(prefix) :]
    return None


def watchlist_show_guids(watchlist: MediaItem) -> set[str]:
    return {
        g
        for g in (
            watchlist.guid,
            watchlist.plex_library_guid,
            library_guid_for_media(watchlist),
        )
        if g
    }
