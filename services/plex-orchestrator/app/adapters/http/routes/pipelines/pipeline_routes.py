"""HTTP routes for multi-step download and ingest pipelines."""
from fastapi import APIRouter, Depends, HTTPException

from app.adapters.http.schemas.antivirus.antivirus_schemas import (
    ScanTorrentAndIngestResponse,
    ScanTorrentRequest,
    ScanTorrentResponse,
)
from app.application.pipelines.ingest.use_cases.scan_and_ingest_torrent_use_case import (
    ScanAndIngestTorrentUseCase,
)
from app.application.pipelines.ingest.use_cases.scan_torrent_use_case import (
    ScanTorrentUseCase,
)
from app.application.pipelines.watchlist.use_cases.process_plex_watchlist_downloads_use_case import (
    ProcessPlexWatchlistDownloadsUseCase,
)
from app.application.pipelines.watchlist.use_cases.reconcile_active_downloads_with_deluge_use_case import (
    ReconcileActiveDownloadsWithDelugeUseCase,
)
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

pipeline_routes = APIRouter(prefix="/pipelines", tags=["pipelines"])


@pipeline_routes.post("/ingest/scan-torrent", response_model=ScanTorrentResponse)
async def scan_torrent(
    request: ScanTorrentRequest,
    use_case: ScanTorrentUseCase = Depends(create_scan_torrent_use_case),
):
    """
    Antivirus scan of a torrent's files only. Does NOT move files or touch Plex/Deluge.

    1. Gets the torrent download by hash from the database
    2. Scans files from the quarantine path with antivirus
    3. Persists the scan record
    4. Returns clean/infected/error

    Use **POST /pipelines/ingest/scan-and-ingest** to scan and then move to Plex library.
    """
    try:
        result = await use_case.execute(request.torrent_hash)
        return ScanTorrentResponse(
            status=result.status,
            message=result.message,
            infected=result.infected,
            virus_name=result.scan_result.virus_name if result.scan_result else None,
            infected_files=result.scan_result.infected_files if result.scan_result else None,
            yara_matches=result.scan_result.yara_matches if result.scan_result else None,
            scanned_files=result.scan_result.scanned_files if result.scan_result else None,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error scanning torrent: {str(e)}")


@pipeline_routes.post(
    "/ingest/scan-and-ingest", response_model=ScanTorrentAndIngestResponse
)
async def scan_and_ingest_torrent(
    request: ScanTorrentRequest,
    use_case: ScanAndIngestTorrentUseCase = Depends(create_scan_and_ingest_torrent_use_case),
):
    """
    Antivirus scan a torrent; if clean move to Plex library and trigger partial scan.
    If infected, remove the torrent and re-add the item to the user's watchlist.

    1. Scans the torrent (antivirus) unless a clean scan is already in the DB (pending move)
    2. If clean: moves to media path, removes from Deluge, triggers Plex partial scan
    3. If move fails or no disk space: status ``pending_move`` — retry later without rescanning
    4. If infected: removes torrent (with data), re-adds to watchlist
    """
    try:
        result = await use_case.execute(request.torrent_hash)
        return ScanTorrentAndIngestResponse(**result.model_dump())
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error running antivirus scan and ingest: {str(e)}"
        )


@pipeline_routes.post("/watchlist/process-downloads")
async def process_plex_watchlist_downloads(
    use_case: ProcessPlexWatchlistDownloadsUseCase = Depends(
        create_process_plex_watchlist_downloads_use_case
    ),
):
    await use_case.execute()
    return {"message": "Watchlist downloads processed successfully"}


@pipeline_routes.post("/watchlist/reconcile-deluge")
async def reconcile_active_downloads_with_deluge(
    use_case: ReconcileActiveDownloadsWithDelugeUseCase = Depends(
        create_reconcile_active_downloads_with_deluge_use_case
    ),
):
    """Reconcile tracked downloads in the DB with Deluge. Removes rows not found in Deluge."""
    result = await use_case.execute()
    if result.get("skipped"):
        return {
            "message": "Reconciliation skipped",
            "skipped": True,
            "reason": result.get("reason"),
            "removed_count": result["removed_count"],
            "updated_count": result.get("updated_count", 0),
            "total_checked": result["total_checked"],
        }
    return {
        "message": "Reconciliation completed successfully",
        "skipped": False,
        "removed_count": result["removed_count"],
        "updated_count": result.get("updated_count", 0),
        "total_checked": result["total_checked"],
    }
