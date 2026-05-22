"""Shared media-type normalization for Plex libraries and torrent ingest."""
from typing import Literal, Optional

PlexLibraryMediaType = Literal["movie", "tvshow", "other"]


def normalize_plex_section_type(section_type: Optional[str]) -> PlexLibraryMediaType:
    """Map Plex library section ``type`` (movie, show, artist, …) to stored kind."""
    if section_type == "movie":
        return "movie"
    if section_type == "show":
        return "tvshow"
    return "other"


def normalize_torrent_media_type(media_type: str) -> PlexLibraryMediaType:
    """Map torrent / watchlist media type strings to library path kind."""
    normalized = media_type.lower()
    if normalized == "movie":
        return "movie"
    if normalized in ("show", "tvshow"):
        return "tvshow"
    return "other"
