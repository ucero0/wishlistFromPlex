from typing import List, Literal, Optional

from pydantic import BaseModel

# Plex user token for server API routes: send as HTTP header (not query/body).
PLEX_USER_TOKEN_HEADER = "X-Plex-Token"


class IsItemInLibraryResponse(BaseModel):
    has_media: bool


class PlexLibrarySectionLocationBody(BaseModel):
    section_id: str
    section_title: str
    media_type: Literal["movie", "tvshow"]
    locations: List[str]


class GetPlexLibraryLocationsResponse(BaseModel):
    sections: List[PlexLibrarySectionLocationBody]


class PlexLibraryPathDiskInfoBody(BaseModel):
    """Plex folder path with volume id and disk usage when this host can see the path."""

    path: str
    volume_root: Optional[str] = None
    total_bytes: Optional[int] = None
    used_bytes: Optional[int] = None
    free_bytes: Optional[int] = None
    error: Optional[str] = None


class PlexLibrarySectionDiskUsageBody(BaseModel):
    section_id: str
    section_title: str
    media_type: Literal["movie", "tvshow"]
    locations: List[PlexLibraryPathDiskInfoBody]


class GetPlexLibraryLocationsDiskUsageResponse(BaseModel):
    sections: List[PlexLibrarySectionDiskUsageBody]
