"""Resolve Plex Discover rating key from a watchlist media item."""
from app.domain.models.media import MediaItem


def discover_rating_key_for_show(watchlist: MediaItem) -> str | None:
    """Plex Discover rating key — only for Plex-sourced watchlist shows."""
    guid = watchlist.guid or ""
    prefix = "plex://show/"
    if guid.startswith(prefix):
        if watchlist.rating_key:
            return watchlist.rating_key
        return guid[len(prefix) :]
    return None
