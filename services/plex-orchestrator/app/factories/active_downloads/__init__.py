"""Active download factories."""
from app.factories.active_downloads.active_downloads_factory import (
    create_get_active_download_by_id_query,
    create_get_active_download_by_uid_query,
    create_get_active_downloads_by_guid_plex_query,
    create_is_guid_plex_downloading_query,
    create_get_active_download_by_guid_prowlarr_query,
    create_get_active_downloads_by_type_query,
    create_get_all_active_downloads_query,
    create_create_active_download_use_case,
    create_update_active_download_use_case,
    create_delete_active_download_use_case,
    create_delete_active_download_by_id_use_case,
)

__all__ = [
    "create_get_active_download_by_id_query",
    "create_get_active_download_by_uid_query",
    "create_get_active_downloads_by_guid_plex_query",
    "create_is_guid_plex_downloading_query",
    "create_get_active_download_by_guid_prowlarr_query",
    "create_get_active_downloads_by_type_query",
    "create_get_all_active_downloads_query",
    "create_create_active_download_use_case",
    "create_update_active_download_use_case",
    "create_delete_active_download_use_case",
    "create_delete_active_download_by_id_use_case",
]

