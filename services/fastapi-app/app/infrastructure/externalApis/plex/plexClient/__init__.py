"""Plex watchlist client package."""
from app.infrastructure.externalApis.plex.plexClient.client import PlexWatchlistClient
from app.infrastructure.externalApis.plex.plexClient.schemas import PlexWatchlistItemDTO

__all__ = [
    "PlexWatchlistClient",
    "PlexWatchlistItemDTO",
]
