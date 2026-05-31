"""Result summary for scheduled Deluge ingest and health maintenance."""
from pydantic import BaseModel


class DelugeTorrentMaintenanceResult(BaseModel):
    completed_checked: int = 0
    ingested: int = 0
    ingest_errors: int = 0
    disk_stats_refreshed: bool = False
    tracking_updated: int = 0
    tracking_removed: int = 0
    unhealthy_checked: int = 0
    unhealthy_removed: int = 0
    skipped_no_active_download: int = 0
