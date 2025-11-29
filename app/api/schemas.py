from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# Token/User Management Schemas
class PlexUserCreate(BaseModel):
    name: str
    token: str


class PlexUserUpdate(BaseModel):
    name: Optional[str] = None
    active: Optional[bool] = None


class PlexUserResponse(BaseModel):
    id: int
    name: str
    token_masked: str
    active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Wishlist Schemas
class WishlistItemResponse(BaseModel):
    id: int
    uid: str
    title: str
    year: Optional[int]
    user_name: Optional[str] = None
    plex_token: Optional[str] = None
    rating_key: Optional[str] = None
    added_at: datetime
    last_seen_at: datetime

    class Config:
        from_attributes = True


class WishlistStatsResponse(BaseModel):
    total_items: int
    items_by_year: dict


# Sync Schemas
class SyncResponse(BaseModel):
    users_processed: int
    items_fetched: int
    new_items: int
    updated_items: int
    total_items: int
    errors: list
    sync_time: str





