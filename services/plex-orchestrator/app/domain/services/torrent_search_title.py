"""Normalize Plex display titles for Prowlarr/torrent search queries."""
import re

_MULTI_SPACE_RE = re.compile(r"\s+")


def normalize_title_for_torrent_search(title: str) -> str:
    """Strip colons from Plex titles so queries match release naming."""
    if not title:
        return title
    normalized = title.replace(":", " ")
    return _MULTI_SPACE_RE.sub(" ", normalized).strip()


def normalize_torrent_search_query(query: str) -> str:
    """Normalize a full Prowlarr search string (title, year, SxxExx, etc.)."""
    if not query:
        return query
    normalized = query.replace(":", " ")
    return _MULTI_SPACE_RE.sub(" ", normalized).strip()
