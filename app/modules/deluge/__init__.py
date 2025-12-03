"""
Deluge module - handles torrent management via Deluge daemon.

This module provides:
- Torrent tracking linked to Plex wishlist items
- Add torrents via magnet links
- Remove torrents with or without data
- Extract torrent information from daemon
"""
from app.modules.deluge.models import TorrentItem, TorrentStatus
from app.modules.deluge.routes import router

__all__ = [
    "TorrentItem",
    "TorrentStatus",
    "router",
]

