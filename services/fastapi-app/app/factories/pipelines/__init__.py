"""FastAPI dependency wrappers for pipeline use cases."""
from app.factories.pipelines.process_plex_watchlist_downloads_factory import (
    create_process_plex_watchlist_downloads_use_case,
)
from app.factories.pipelines.reconcile_deluge_downloads_factory import (
    create_reconcile_active_downloads_with_deluge_use_case,
)
from app.factories.pipelines.scan_and_ingest_torrent_factory import (
    create_scan_and_ingest_torrent_use_case,
    create_scan_torrent_use_case,
)

__all__ = [
    "create_process_plex_watchlist_downloads_use_case",
    "create_reconcile_active_downloads_with_deluge_use_case",
    "create_scan_torrent_use_case",
    "create_scan_and_ingest_torrent_use_case",
]
