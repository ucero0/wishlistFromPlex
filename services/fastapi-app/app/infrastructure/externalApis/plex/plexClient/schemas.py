"""External schemas for Plex API."""
from pydantic import BaseModel, ConfigDict

class PlexWatchlistItemDTO(BaseModel):
    model_config = ConfigDict(extra="ignore")

    guid: str
    ratingKey: str
    title: str
    type: str               # "movie" | "show"
    year: int

