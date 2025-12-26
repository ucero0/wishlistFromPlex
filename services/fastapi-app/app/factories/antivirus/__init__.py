"""Antivirus factories."""
from app.factories.antivirus.antivirusFactory import (
    create_check_infected_by_guid_prowlarr_query,
    create_get_antivirus_scan_by_id_query,
    create_get_antivirus_scans_by_guid_prowlarr_query,
    create_get_antivirus_scan_by_file_path_query,
    create_get_infected_items_query,
    create_get_clean_items_query,
    create_get_all_antivirus_scans_query,
    create_create_antivirus_scan_use_case,
    create_update_antivirus_scan_use_case,
    create_delete_antivirus_scan_use_case,
    create_delete_antivirus_scan_by_id_use_case,
    create_delete_antivirus_scans_by_guid_prowlarr_use_case,
)

__all__ = [
    "create_check_infected_by_guid_prowlarr_query",
    "create_get_antivirus_scan_by_id_query",
    "create_get_antivirus_scans_by_guid_prowlarr_query",
    "create_get_antivirus_scan_by_file_path_query",
    "create_get_infected_items_query",
    "create_get_clean_items_query",
    "create_get_all_antivirus_scans_query",
    "create_create_antivirus_scan_use_case",
    "create_update_antivirus_scan_use_case",
    "create_delete_antivirus_scan_use_case",
    "create_delete_antivirus_scan_by_id_use_case",
    "create_delete_antivirus_scans_by_guid_prowlarr_use_case",
]

