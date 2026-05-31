"""Internal domain model for a media item."""
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict


class MediaType(str, Enum):
    """Media type enumeration - domain model."""

    MOVIE = "movie"
    SHOW = "show"
    TVSHOW = "tvshow"  # alias used by some integrations
    SEASON = "season"
    EPISODE = "episode"


class MediaItem(BaseModel):
    """Internal domain model for a media item."""

    model_config = ConfigDict(from_attributes=False)

    guid: str
    rating_key: Optional[str] = None
    title: Optional[str] = None
    year: Optional[int] = None
    type: Optional[MediaType] = None
    plex_library_guid: Optional[str] = None
