"""Watchlist row with owning user context."""
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.domain.models.media import MediaItem
from app.domain.models.watchlist_source import WatchlistSource


class WatchlistItemForUser(BaseModel):
    """A watchlist item and the user whose list it came from."""

    model_config = ConfigDict(from_attributes=False)

    item: MediaItem
    source: WatchlistSource = WatchlistSource.PLEX
    plex_user_id: Optional[int] = None
    plex_user_token: Optional[str] = None
    tmdb_user_id: Optional[int] = None
    tmdb_account_id: Optional[int] = None
    tmdb_access_token: Optional[str] = None

    def user_token(self) -> Optional[str]:
        if self.source == WatchlistSource.PLEX:
            return self.plex_user_token
        return self.tmdb_access_token
