"""Watchlist row with owning user context."""
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.domain.models.media import MediaItem
from app.domain.models.watchlist_source import WatchlistSource
from app.domain.models.watchlist_subscriber import WatchlistSubscriber
from app.domain.services.tmdb_guid import parse_tmdb_guid


def subscriber_from_entry(entry: "WatchlistItemForUser") -> WatchlistSubscriber:
    tmdb_media_id: int | None = None
    if entry.source == WatchlistSource.TMDB:
        parsed = parse_tmdb_guid(entry.item.guid or "")
        if parsed:
            tmdb_media_id = parsed[1]
        elif entry.item.rating_key and entry.item.rating_key.isdigit():
            tmdb_media_id = int(entry.item.rating_key)

    plex_watchlist_rating_key = None
    if entry.source == WatchlistSource.PLEX:
        plex_watchlist_rating_key = entry.plex_watchlist_rating_key or entry.item.rating_key

    return WatchlistSubscriber(
        source=entry.source,
        plex_user_id=entry.plex_user_id,
        plex_user_token=entry.plex_user_token,
        plex_watchlist_rating_key=plex_watchlist_rating_key,
        tmdb_user_id=entry.tmdb_user_id,
        tmdb_account_id=entry.tmdb_account_id,
        tmdb_access_token=entry.tmdb_access_token,
        tmdb_media_id=tmdb_media_id,
    )


class WatchlistItemForUser(BaseModel):
    """A watchlist item and the user(s) whose list(s) it came from."""

    model_config = ConfigDict(from_attributes=False)

    item: MediaItem
    source: WatchlistSource = WatchlistSource.PLEX
    plex_user_id: Optional[int] = None
    plex_user_token: Optional[str] = None
    plex_watchlist_rating_key: Optional[str] = None
    tmdb_user_id: Optional[int] = None
    tmdb_account_id: Optional[int] = None
    tmdb_access_token: Optional[str] = None
    subscribers: list[WatchlistSubscriber] = Field(default_factory=list)

    def all_subscribers(self) -> list[WatchlistSubscriber]:
        if self.subscribers:
            return self.subscribers
        return [subscriber_from_entry(self)]

    def user_token(self) -> Optional[str]:
        if self.source == WatchlistSource.PLEX:
            return self.plex_user_token
        return self.tmdb_access_token
