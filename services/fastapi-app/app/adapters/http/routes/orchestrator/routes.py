from fastapi import APIRouter, Depends, HTTPException
from app.factories.orchestrators.findFiles2Download import create_download_watch_list_media_use_case
from app.factories.orchestrators.syncTorrentDownloadWithDelugeFactory import create_sync_torrent_download_with_deluge_use_case
from app.factories.orchestrators.antivirusScanTorrentAndIngestFactory import (
    create_antivirus_scan_torrent_use_case,
    create_antivirus_scan_torrent_and_ingest_use_case,
)
from app.application.orchestrators.useCases.downloadWatchListMedia import DownloadWatchListMediaUseCase
from app.application.orchestrators.useCases.syncTorrentDownloadWithDeluge import SyncTorrentDownloadWithDelugeUseCase
from app.application.orchestrators.useCases.antivirusScanTorrent import AntivirusScanTorrentUseCase
from app.application.orchestrators.useCases.antivirusScanTorrentAndIngest import (
    AntivirusScanTorrentAndIngestUseCase,
)
from app.adapters.http.schemas.antivirus.antivirusSchemas import (
    ScanTorrentRequest,
    ScanTorrentResponse,
    ScanTorrentAndIngestResponse,
)

orchestratorRoutes = APIRouter(prefix="/orchestrator", tags=["orchestrator"])


@orchestratorRoutes.post("/antivirus-scan-torrent", response_model=ScanTorrentResponse)
async def antivirus_scan_torrent(
    request: ScanTorrentRequest,
    use_case: AntivirusScanTorrentUseCase = Depends(create_antivirus_scan_torrent_use_case),
):
    """
    Antivirus scan of a torrent's files only. Does NOT move files or touch Plex/Deluge.

    1. Gets the torrent download by hash from the database
    2. Scans files from the quarantine path with antivirus
    3. Persists the scan record
    4. Returns clean/infected/error

    Use **POST /orchestrator/antivirus-scan-torrent-and-ingest** to scan and then move to Plex library.
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


@orchestratorRoutes.post("/antivirus-scan-torrent-and-ingest", response_model=ScanTorrentAndIngestResponse)
async def antivirus_scan_torrent_and_ingest(
    request: ScanTorrentRequest,
    use_case: AntivirusScanTorrentAndIngestUseCase = Depends(
        create_antivirus_scan_torrent_and_ingest_use_case
    ),
):
    """
    Antivirus scan a torrent; if clean move to Plex library and trigger partial scan.
    If infected, remove the torrent and re-add the item to the user's watchlist.

    1. Scans the torrent (antivirus)
    2. If clean: moves to media path, removes from Deluge, triggers Plex partial scan
    3. If infected: removes torrent (with data), re-adds to watchlist
    """
    try:
        result = await use_case.execute(request.torrent_hash)
        return ScanTorrentAndIngestResponse(**result.model_dump())
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error running antivirus scan and ingest: {str(e)}"
        )


@orchestratorRoutes.post("/download-watch-list-media")
async def download_watch_list_media(use_case: DownloadWatchListMediaUseCase = Depends(create_download_watch_list_media_use_case)):
    await use_case.execute()
    return {"message": "Watch list media downloaded successfully"}

@orchestratorRoutes.post("/sync-torrent-download-with-deluge")
async def sync_torrent_download_with_deluge(
    use_case: SyncTorrentDownloadWithDelugeUseCase = Depends(create_sync_torrent_download_with_deluge_use_case)
):
    """Sync torrent download DB with Deluge status. Removes DB entries not found in Deluge."""
    result = await use_case.execute()
    return {
        "message": "Sync completed successfully",
        "removed_count": result["removed_count"],
        "total_checked": result["total_checked"]
    }