from typing import List, Literal

from pydantic import BaseModel


class IsItemInLibraryResponse(BaseModel):
    has_media: bool


class PlexLibrarySectionLocationBody(BaseModel):
    section_id: str
    section_title: str
    media_type: Literal["movie", "tvshow", "other"]
    locations: List[str]


class GetPlexLibraryLocationsResponse(BaseModel):
    sections: List[PlexLibrarySectionLocationBody]


class SyncPlexLibraryLocationsResponse(BaseModel):
    """Same layout as live Plex query, plus DB sync stats."""

    sections: List[PlexLibrarySectionLocationBody]
    synced_from_server: int
    active_in_database: int
