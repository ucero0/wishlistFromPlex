from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from enum import Enum


class MediaType(str, Enum):
    """Media type enumeration - domain model."""
    MOVIE = "movie"
    SHOW = "show"
    TVSHOW = "tvshow"  # alias used by some integrations
    SEASON = "season"
    EPISODE = "episode"

class MediaItem(BaseModel):
    """Internal domain model for a media item."""
    model_config = ConfigDict(populate_by_name=True)

    guid: str
    rating_key: Optional[str] = Field(default=None, alias="ratingKey")
    title: Optional[str] = None
    year: Optional[int] = None
    type: Optional[MediaType] = None

