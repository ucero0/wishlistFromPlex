"""Domain model for torrent downloads."""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime


class TorrentDownload(BaseModel):
    """Domain model for a torrent download item."""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: Optional[int] = None
    plex_guid: str = Field(alias="guidPlex")
    watchlist_item_id: Optional[str] = Field(default=None, alias="ratingKey")
    plex_user_token: Optional[str] = Field(default=None, alias="plexUserToken")
    prowlarr_guid: str = Field(alias="guidProwlarr")
    uid: str
    title: str
    file_name: Optional[str] = Field(default=None, alias="fileName")
    year: Optional[int] = None
    type: str  # "movie" or "show"
    season: Optional[int] = None
    episode: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

