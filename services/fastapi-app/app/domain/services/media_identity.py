"""Normalize title/year/type for cross-user duplicate detection."""
from __future__ import annotations

from typing import Optional


def normalize_title(title: Optional[str]) -> Optional[str]:
    if not title:
        return None
    normalized = " ".join(title.strip().lower().split())
    return normalized or None


def normalize_media_type_for_queue_match(media_type: Optional[str]) -> Optional[str]:
    """Map Plex/torrent/deferred types to ``movie`` or ``show`` for queue matching."""
    if media_type is None:
        return None
    raw = str(media_type).lower()
    if raw.endswith(".movie"):
        return "movie"
    if raw.endswith(".show") or raw.endswith(".tvshow"):
        return "show"
    if raw in ("movie", "show", "tvshow"):
        return "show" if raw == "tvshow" else raw
    return raw
