"""Map domain tracking models to HTTP response schemas."""
from app.adapters.http.schemas.tracking.tracking_schemas import (
    AntivirusScanItem,
    ActiveDownloadItem,
)
from app.domain.models.antivirus_scan_status import is_clean_pending_ingest
from app.domain.models.antivirus_scan import AntivirusScan
from app.domain.models.active_download import ActiveDownload


def to_antivirus_scan_item(
    scan: AntivirusScan, *, quarantine_root: str
) -> AntivirusScanItem:
    return AntivirusScanItem(
        id=scan.id or 0,
        guid_prowlarr=scan.prowlarr_guid,
        file_path=scan.file_path,
        folder_path_src=scan.source_folder_path,
        folder_path_dst=scan.destination_folder_path,
        planned_destination=scan.planned_destination_path,
        ingest_error=scan.ingest_error,
        infected=scan.is_infected,
        scan_datetime=scan.scanned_at,
        created_at=scan.created_at,
        updated_at=scan.updated_at,
        pending_ingest=is_clean_pending_ingest(scan, quarantine_root),
    )


def to_active_download_item(row: ActiveDownload) -> ActiveDownloadItem:
    return ActiveDownloadItem(
        id=row.id or 0,
        guid_plex=row.plex_guid,
        rating_key=row.watchlist_item_id,
        guid_prowlarr=row.prowlarr_guid,
        uid=row.uid,
        title=row.title,
        file_name=row.file_name,
        year=row.year,
        type=row.type,
        season=row.season,
        episode=row.episode,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )
