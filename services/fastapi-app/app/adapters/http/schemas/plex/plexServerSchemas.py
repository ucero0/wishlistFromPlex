from typing import List, Literal, Optional

from pydantic import BaseModel

from app.adapters.http.schemas.plex.plexLibraryPathSchemas import (
    PlexLibraryPathDiskInfoBody,
    PlexLibrarySectionDiskUsageBody,
)

# Plex user token for server API routes: send as HTTP header (not query/body).
PLEX_USER_TOKEN_HEADER = "X-Plex-Token"


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


class GetPlexLibraryLocationsDiskUsageResponse(BaseModel):
    sections: List[PlexLibrarySectionDiskUsageBody]
