"""Torrent download factories."""
from app.factories.torrentDownload.torrentDownloadFactory import (
    create_get_torrent_download_by_id_query,
    create_get_torrent_download_by_uid_query,
    create_get_torrent_downloads_by_guid_plex_query,
    create_is_guid_plex_downloading_query,
    create_get_torrent_download_by_guid_prowlarr_query,
    create_get_torrent_downloads_by_type_query,
    create_get_all_torrent_downloads_query,
    create_create_torrent_download_use_case,
    create_update_torrent_download_use_case,
    create_delete_torrent_download_use_case,
    create_delete_torrent_download_by_id_use_case,
)

__all__ = [
    "create_get_torrent_download_by_id_query",
    "create_get_torrent_download_by_uid_query",
    "create_get_torrent_downloads_by_guid_plex_query",
    "create_is_guid_plex_downloading_query",
    "create_get_torrent_download_by_guid_prowlarr_query",
    "create_get_torrent_downloads_by_type_query",
    "create_get_all_torrent_downloads_query",
    "create_create_torrent_download_use_case",
    "create_update_torrent_download_use_case",
    "create_delete_torrent_download_use_case",
    "create_delete_torrent_download_by_id_use_case",
]

