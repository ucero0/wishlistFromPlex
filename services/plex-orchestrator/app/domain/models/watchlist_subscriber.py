"""One Plex or TMDB account that has a title on their watchlist."""
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.domain.models.watchlist_source import WatchlistSource


class WatchlistSubscriber(BaseModel):
    model_config = ConfigDict(from_attributes=False)

    source: WatchlistSource
    plex_user_id: Optional[int] = None
    plex_user_token: Optional[str] = None
    plex_watchlist_rating_key: Optional[str] = None
    tmdb_user_id: Optional[int] = None
    tmdb_account_id: Optional[int] = None
    tmdb_access_token: Optional[str] = None
    tmdb_media_id: Optional[int] = None

    def dedupe_key(self) -> tuple[str, int | None, int | None]:
        return (self.source.value, self.plex_user_id, self.tmdb_user_id)
