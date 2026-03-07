"""Blacklist torrent factories."""
from app.factories.blacklist_torrent.blacklist_torrent_factory import (
    create_is_blacklisted_by_guid_prowlarr_query,
    create_add_torrent_to_blacklist_use_case,
    create_add_torrent_to_blacklist_by_hash_use_case,
    create_list_blacklist_torrents_query,
    create_get_blacklist_torrent_by_guid_query,
    create_remove_torrent_from_blacklist_use_case,
)

__all__ = [
    "create_is_blacklisted_by_guid_prowlarr_query",
    "create_add_torrent_to_blacklist_use_case",
    "create_add_torrent_to_blacklist_by_hash_use_case",
    "create_list_blacklist_torrents_query",
    "create_get_blacklist_torrent_by_guid_query",
    "create_remove_torrent_from_blacklist_use_case",
]
