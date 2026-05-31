"""Domain model for torrent downloads."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ActiveDownload(BaseModel):
    """Domain model for a torrent download item."""

    model_config = ConfigDict(from_attributes=False)

    id: Optional[int] = None
    plex_guid: str
    plex_library_guid: Optional[str] = None
    watchlist_item_id: Optional[str] = None
    plex_user_token: Optional[str] = None
    watchlist_source: Optional[str] = None
    tmdb_media_id: Optional[int] = None
    tmdb_account_id: Optional[int] = None
    prowlarr_guid: str
    uid: str
    title: str
    file_name: Optional[str] = None
    year: Optional[int] = None
    type: str  # "movie" or "show"
    season: Optional[int] = None
    episode: Optional[int] = None
    episode_name: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
