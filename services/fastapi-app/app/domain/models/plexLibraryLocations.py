"""Plex library section paths — domain view of server library layout."""
from __future__ import annotations

from typing import List, Literal

from pydantic import BaseModel

PlexLibrarySectionMediaKind = Literal["movie", "tvshow", "other"]


class PlexLibrarySectionLocation(BaseModel):
    """One Plex library section (movie or TV) and its root paths on disk."""

    section_id: str
    section_title: str
    media_type: PlexLibrarySectionMediaKind
    locations: List[str]


class PlexLibraryLocationsByMedia(BaseModel):
    """Movie and TV show library sections with their configured folder paths."""

    sections: List[PlexLibrarySectionLocation]
