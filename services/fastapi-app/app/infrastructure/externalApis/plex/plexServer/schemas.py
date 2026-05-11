"""Plex Server external API schemas - raw responses from Plex Server API."""
from pydantic import BaseModel, ConfigDict
from typing import List, Literal, Any, Dict


class PlexLibraryLocationItem(BaseModel):
    """Plex library location info for movie/tvshow sections."""
    section_id: str
    section_title: str
    media_type: Literal["movie", "tvshow"]
    locations: List[str]


class PlexLibraryLocationsByMediaResponse(BaseModel):
    """List of Plex library locations grouped by media type."""
    items: List[PlexLibraryLocationItem]


class PlexLibraryMetadata(BaseModel):
    """Plex library/all metadata wrapper."""
    model_config = ConfigDict(extra="allow")


class PlexLibraryAllResponse(BaseModel):
    """Raw Plex /library/all response schema."""
    MediaContainer: Dict[str, Any]

