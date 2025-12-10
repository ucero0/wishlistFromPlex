"""Plex module Pydantic schemas."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class BaseSchema(BaseModel):
    """Base schema with common configuration."""
    class Config:
        from_attributes = True


# Enums
class MediaTypeEnum(str, Enum):
    """Media type enumeration for API."""
    MOVIE = "movie"
    SHOW = "show"
    SEASON = "season"
    EPISODE = "episode"


# Plex User Schemas
class PlexUserCreate(BaseModel):
    """Schema for creating a new Plex user."""
    name: str
    token: str


class PlexUserUpdate(BaseModel):
    """Schema for updating an existing Plex user."""
    name: Optional[str] = None
    active: Optional[bool] = None


class PlexUserResponse(BaseSchema):
    """Schema for Plex user responses."""
    id: int
    name: str
    token_masked: str
    active: bool
    created_at: datetime
    updated_at: datetime


# Wishlist Item Schemas
class WishlistItemResponse(BaseSchema):
    """Schema for wishlist item responses."""
    id: int
    guid: str
    rating_key: Optional[str] = None
    title: str
    year: Optional[int] = None
    media_type: Optional[str] = None
    summary: Optional[str] = None
    thumb: Optional[str] = None
    art: Optional[str] = None
    content_rating: Optional[str] = None
    studio: Optional[str] = None
    added_at: datetime
    last_seen_at: datetime


class WishlistStatsResponse(BaseSchema):
    """Schema for wishlist statistics."""
    total_items: int
    items_by_year: dict
    items_by_type: Optional[dict] = None


# Plex API Data Schemas
class PlexItemData(BaseModel):
    """Schema for normalized Plex item data from API."""
    guid: str
    ratingKey: Optional[str] = None
    title: str
    year: Optional[int] = None
    type: Optional[str] = Field(None, alias="mediaType")
    summary: Optional[str] = None
    thumb: Optional[str] = None
    art: Optional[str] = None
    contentRating: Optional[str] = None
    studio: Optional[str] = None

    class Config:
        from_attributes = True
        populate_by_name = True


class PlexAccountInfo(BaseModel):
    """Schema for Plex account information."""
    username: str
    email: Optional[str] = None
    title: Optional[str] = None
    uuid: str


# Sync Schemas
class SyncResponse(BaseModel):
    """Schema for sync operation responses."""
    users_processed: int
    items_fetched: int
    new_items: int
    updated_items: int
    total_items: int
    errors: List[str]
    sync_time: str

