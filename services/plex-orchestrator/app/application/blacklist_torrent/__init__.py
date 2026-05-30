"""Blacklist torrent application (do not send to Deluge: infected, unhealthy, etc.)."""
from app.application.blacklist_torrent.queries import IsBlacklistedByGuidProwlarrQuery
from app.application.blacklist_torrent.use_cases import AddTorrentToBlacklistUseCase

__all__ = [
    "IsBlacklistedByGuidProwlarrQuery",
    "AddTorrentToBlacklistUseCase",
]
