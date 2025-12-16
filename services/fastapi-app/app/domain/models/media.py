from pydantic import BaseModel
from typing import Optional
from enum import Enum


class MediaType(str, Enum):
    """Media type enumeration - domain model."""
    MOVIE = "movie"
    SHOW = "show"
    SEASON = "season"
    EPISODE = "episode"

class MediaItem(BaseModel):
    """Internal domain model for a media item."""
    guid: str
    ratingKey: Optional[str] = None
    title: Optional[str] = None
    year: Optional[int] = None
    type: Optional[MediaType] = None