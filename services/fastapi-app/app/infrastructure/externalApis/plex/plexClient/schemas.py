"""External schemas for Plex API."""
from pydantic import BaseModel

class PlexWatchlistItemDTO(BaseModel):
    guid: str
    ratingKey: str
    title: str
    type: str               # "movie" | "show"
    year: int

    class Config:
        extra = "ignore"    # Plex adds lots of fields
