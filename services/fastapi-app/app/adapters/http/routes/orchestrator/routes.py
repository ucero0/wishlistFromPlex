from fastapi import APIRouter, Depends
from app.factories.orchestrators.findFiles2Download import create_download_watch_list_media_use_case
from app.factories.orchestrators.syncTorrentDownloadWithDelugeFactory import create_sync_torrent_download_with_deluge_use_case
from app.application.orchestrators.useCases.downloadWatchListMedia import DownloadWatchListMediaUseCase
from app.application.orchestrators.useCases.syncTorrentDownloadWithDeluge import SyncTorrentDownloadWithDelugeUseCase

orchestratorRoutes = APIRouter(prefix="/orchestrator", tags=["orchestrator"])

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