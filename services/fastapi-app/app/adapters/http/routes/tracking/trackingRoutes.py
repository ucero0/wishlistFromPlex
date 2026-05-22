"""Read-only API for pipeline tracking rows stored in PostgreSQL."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.adapters.http.routes.tracking.mappers import (
    to_antivirus_scan_item,
    to_torrent_download_item,
)
from app.adapters.http.mappers.disk_size_format import format_bytes_for_display
from app.adapters.http.schemas.tracking.trackingSchemas import (
    AntivirusScanItem,
    AntivirusScanListResponse,
    DeferredTorrentDownloadItem,
    DeferredTorrentDownloadListResponse,
    ProcessDeferredTorrentDownloadsResponse,
    TorrentDownloadItem,
    TorrentDownloadListResponse,
)
from app.application.deferredTorrent.queries.listDeferredTorrentDownloads import (
    ListDeferredTorrentDownloadsQuery,
)
from app.application.antivirus.queries import (
    GetAllAntivirusScansQuery,
    GetAntivirusScanByIdQuery,
    GetAntivirusScansByGuidProwlarrQuery,
)
from app.application.torrentDownload.queries import (
    GetAllTorrentDownloadsQuery,
    GetTorrentDownloadByIdQuery,
    GetTorrentDownloadByGuidProwlarrQuery,
    GetTorrentDownloadByUidQuery,
)
from app.core.config import settings
from app.factories.antivirus.antivirusFactory import (
    create_get_all_antivirus_scans_query,
    create_get_antivirus_scan_by_id_query,
    create_get_antivirus_scans_by_guid_prowlarr_query,
)
from app.application.deferredTorrent.useCases.processDeferredTorrentDownloads import (
    ProcessDeferredTorrentDownloadsUseCase,
)
from app.factories.deferredTorrent.deferredTorrentFactory import (
    create_list_deferred_torrent_downloads_query,
    create_process_deferred_torrent_downloads_use_case,
)
from app.factories.torrentDownload.torrentDownloadFactory import (
    create_get_all_torrent_downloads_query,
    create_get_torrent_download_by_id_query,
    create_get_torrent_download_by_guid_prowlarr_query,
    create_get_torrent_download_by_uid_query,
)

trackingRoutes = APIRouter(prefix="/tracking", tags=["tracking"])


@trackingRoutes.get("/antivirus-scans", response_model=AntivirusScanListResponse)
async def list_antivirus_scans(
    infected: Optional[bool] = Query(
        None, description="Filter by infection status"
    ),
    guid_prowlarr: Optional[str] = Query(
        None, description="Filter by Prowlarr GUID"
    ),
    pending_ingest: Optional[bool] = Query(
        None,
        description="Clean scan still in quarantine waiting for library move",
    ),
    all_scans_query: GetAllAntivirusScansQuery = Depends(
        create_get_all_antivirus_scans_query
    ),
    by_guid_query: GetAntivirusScansByGuidProwlarrQuery = Depends(
        create_get_antivirus_scans_by_guid_prowlarr_query
    ),
):
    """List antivirus scan records from the database."""
    quarantine_root = settings.container_deluge_quarantine_path
    rows = (
        await by_guid_query.execute(guid_prowlarr)
        if guid_prowlarr
        else await all_scans_query.execute()
    )
    if infected is not None:
        rows = [r for r in rows if r.is_infected is infected]
    if pending_ingest is not None:
        rows = [
            r
            for r in rows
            if to_antivirus_scan_item(r, quarantine_root=quarantine_root).pending_ingest
            is pending_ingest
        ]
    items = [to_antivirus_scan_item(r, quarantine_root=quarantine_root) for r in rows]
    return AntivirusScanListResponse(items=items, total=len(items))


@trackingRoutes.get("/antivirus-scans/{scan_id}", response_model=AntivirusScanItem)
async def get_antivirus_scan(
    scan_id: int,
    query: GetAntivirusScanByIdQuery = Depends(create_get_antivirus_scan_by_id_query),
):
    """Get one antivirus scan record by id."""
    row = await query.execute(scan_id)
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Antivirus scan {scan_id} not found",
        )
    return to_antivirus_scan_item(
        row, quarantine_root=settings.container_deluge_quarantine_path
    )


@trackingRoutes.get("/torrent-downloads", response_model=TorrentDownloadListResponse)
async def list_torrent_downloads(
    query: GetAllTorrentDownloadsQuery = Depends(create_get_all_torrent_downloads_query),
):
    """List torrent download tracking rows from the database."""
    rows = await query.execute()
    items = [to_torrent_download_item(r) for r in rows]
    return TorrentDownloadListResponse(items=items, total=len(items))


@trackingRoutes.get(
    "/torrent-downloads/by-uid/{uid}",
    response_model=TorrentDownloadItem,
)
async def get_torrent_download_by_uid(
    uid: str,
    query: GetTorrentDownloadByUidQuery = Depends(create_get_torrent_download_by_uid_query),
):
    """Get torrent download by Deluge torrent hash (uid)."""
    row = await query.execute(uid)
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Torrent download with uid {uid} not found",
        )
    return to_torrent_download_item(row)


@trackingRoutes.get(
    "/torrent-downloads/by-guid-prowlarr/{guid_prowlarr}",
    response_model=TorrentDownloadItem,
)
async def get_torrent_download_by_guid_prowlarr(
    guid_prowlarr: str,
    query: GetTorrentDownloadByGuidProwlarrQuery = Depends(
        create_get_torrent_download_by_guid_prowlarr_query
    ),
):
    """Get torrent download by Prowlarr GUID."""
    row = await query.execute(guid_prowlarr)
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Torrent download for guid_prowlarr {guid_prowlarr} not found",
        )
    return to_torrent_download_item(row)


@trackingRoutes.get("/torrent-downloads/{download_id}", response_model=TorrentDownloadItem)
async def get_torrent_download(
    download_id: int,
    query: GetTorrentDownloadByIdQuery = Depends(create_get_torrent_download_by_id_query),
):
    """Get one torrent download row by id."""
    row = await query.execute(download_id)
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Torrent download {download_id} not found",
        )
    return to_torrent_download_item(row)


@trackingRoutes.get(
    "/deferred-downloads",
    response_model=DeferredTorrentDownloadListResponse,
    summary="List torrents waiting for download volume space",
)
async def list_deferred_torrent_downloads(
    limit: int = Query(100, ge=1, le=500),
    query: ListDeferredTorrentDownloadsQuery = Depends(
        create_list_deferred_torrent_downloads_query
    ),
):
    """
    Prowlarr/Deluge sends are postponed here when the quarantine/download volume is full.

    Magnets are kept via ``guid_prowlarr`` + ``indexer_id``; released automatically when space is available.
    """
    rows = await query.execute(limit=limit)
    items = [
        DeferredTorrentDownloadItem(
            id=r.id or 0,
            guid_plex=r.guid_plex,
            rating_key=r.rating_key,
            guid_prowlarr=r.guid_prowlarr,
            indexer_id=r.indexer_id,
            torrent_title=r.torrent_title,
            media_title=r.media_title,
            year=r.year,
            media_type=r.media_type,
            search_query=r.search_query,
            size=format_bytes_for_display(r.size_bytes),
            status=r.status,
            defer_reason=r.defer_reason,
            attempt_count=r.attempt_count,
            created_at=r.created_at,
            sent_at=r.sent_at,
        )
        for r in rows
    ]
    return DeferredTorrentDownloadListResponse(
        items=items,
        total=len(items),
        download_volume_path=settings.container_deluge_quarantine_path,
    )


@trackingRoutes.post(
    "/deferred-downloads/process",
    response_model=ProcessDeferredTorrentDownloadsResponse,
    summary="Process deferred torrents when download volume has space",
)
async def process_deferred_torrent_downloads(
    limit: int = Query(20, ge=1, le=100, description="Max pending rows to try"),
    use_case: ProcessDeferredTorrentDownloadsUseCase = Depends(
        create_process_deferred_torrent_downloads_use_case
    ),
):
    """
    Manually drain the deferred queue (same logic as the scheduler).

    Sends magnets to Prowlarr/Deluge when the quarantine volume has enough free space.
    """
    result = await use_case.execute(limit=limit)
    return ProcessDeferredTorrentDownloadsResponse(
        checked=result.checked,
        sent=result.sent,
        still_pending=result.still_pending,
        failed=result.failed,
    )
