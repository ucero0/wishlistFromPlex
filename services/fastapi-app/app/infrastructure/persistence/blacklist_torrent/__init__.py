"""Blacklist torrent persistence."""
from app.infrastructure.persistence.blacklist_torrent.model import BlacklistTorrentOrm
from app.infrastructure.persistence.blacklist_torrent.repo import BlacklistTorrentRepository

__all__ = ["BlacklistTorrentOrm", "BlacklistTorrentRepository"]
