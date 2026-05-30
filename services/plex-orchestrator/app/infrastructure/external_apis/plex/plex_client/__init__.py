"""Plex watchlist client package."""
from app.infrastructure.external_apis.plex.plex_client.client import PlexWatchlistClient
from app.infrastructure.external_apis.plex.plex_client.schemas import PlexWatchlistItemDTO

__all__ = [
    "PlexWatchlistClient",
    "PlexWatchlistItemDTO",
]
