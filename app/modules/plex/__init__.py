"""
Plex module - handles Plex watchlist sync and management.

This module provides:
- Watchlist sync from Plex accounts
- Wishlist item management
- Plex user token management
"""
from app.modules.plex.models import PlexUser, WishlistItem, WishlistItemSource, MediaType
from app.modules.plex.routes import router

__all__ = [
    "PlexUser",
    "WishlistItem",
    "WishlistItemSource",
    "MediaType",
    "router",
]

