"""Blacklist torrent queries."""
from app.application.blacklist_torrent.queries.is_blacklisted_by_guid_prowlarr import (
    IsBlacklistedByGuidProwlarrQuery,
)
from app.application.blacklist_torrent.queries.list_blacklist_torrents import (
    ListBlacklistTorrentsQuery,
)
from app.application.blacklist_torrent.queries.get_blacklist_torrent_by_guid import (
    GetBlacklistTorrentByGuidQuery,
)

__all__ = [
    "IsBlacklistedByGuidProwlarrQuery",
    "ListBlacklistTorrentsQuery",
    "GetBlacklistTorrentByGuidQuery",
]
