"""Watchlist row with owning Plex user context."""
from pydantic import BaseModel, ConfigDict

from app.domain.models.media import MediaItem


class WatchlistItemForUser(BaseModel):
    """A Plex watchlist item and the user whose list it came from."""

    model_config = ConfigDict(from_attributes=False)

    item: MediaItem
    plex_user_id: int
    plex_user_token: str
