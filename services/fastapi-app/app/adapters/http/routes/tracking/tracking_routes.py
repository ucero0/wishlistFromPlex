"""Read-only API for pipeline tracking rows stored in PostgreSQL."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.adapters.http.routes.tracking.mappers import (
    to_antivirus_scan_item,
    to_active_download_item,
)
from app.core.formatting import format_bytes_for_display
from app.adapters.http.schemas.tracking.tracking_schemas import (
    AntivirusScanItem,
    AntivirusScanListResponse,
    DeferredDownloadItem,
    DeferredDownloadListResponse,
    ProcessDeferredDownloadsResponse,
    ActiveDownloadItem,
    ActiveDownloadListResponse,
)
from app.application.deferred_downloads.queries.list_deferred_downloads_query import (
    ListDeferredDownloadsQuery,
)
from app.application.antivirus.queries import (
    GetAllAntivirusScansQuery,
    GetAntivirusScanByIdQuery,
    GetAntivirusScansByGuidProwlarrQuery,
)
from app.application.active_downloads.queries import (
    GetAllActiveDownloadsQuery,
    GetActiveDownloadByIdQuery,
    GetActiveDownloadByGuidProwlarrQuery,
    GetActiveDownloadByUidQuery,
)
from app.core.config import settings
from app.factories.antivirus.antivirus_factory import (
    create_get_all_antivirus_scans_query,
    create_get_antivirus_scan_by_id_query,
    create_get_antivirus_scans_by_guid_prowlarr_query,
)
from app.application.deferred_downloads.use_cases.process_deferred_downloads_use_case import (
    ProcessDeferredDownloadsUseCase,
)
from app.factories.deferred_downloads.deferred_downloads_factory import (
    create_list_deferred_downloads_query,
    create_process_deferred_downloads_use_case,
)
from app.factories.active_downloads.active_downloads_factory import (
    create_get_all_active_downloads_query,
    create_get_active_download_by_id_query,
    create_get_active_download_by_guid_prowlarr_query,
    create_get_active_download_by_uid_query,
)

tracking_routes = APIRouter(prefix="/tracking", tags=["tracking"])


@tracking_routes.get("/antivirus-scans", response_model=AntivirusScanListResponse)
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


@tracking_routes.get("/antivirus-scans/{scan_id}", response_model=AntivirusScanItem)
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


@tracking_routes.get("/active-downloads", response_model=ActiveDownloadListResponse)
async def list_active_downloads(
    query: GetAllActiveDownloadsQuery = Depends(create_get_all_active_downloads_query),
):
    """List torrent download tracking rows from the database."""
    rows = await query.execute()
    items = [to_active_download_item(r) for r in rows]
    return ActiveDownloadListResponse(items=items, total=len(items))


@tracking_routes.get(
    "/active-downloads/by-uid/{uid}",
    response_model=ActiveDownloadItem,
)
async def get_active_download_by_uid(
    uid: str,
    query: GetActiveDownloadByUidQuery = Depends(create_get_active_download_by_uid_query),
):
    """Get torrent download by Deluge torrent hash (uid)."""
    row = await query.execute(uid)
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Torrent download with uid {uid} not found",
        )
    return to_active_download_item(row)


@tracking_routes.get(
    "/active-downloads/by-guid-prowlarr/{guid_prowlarr}",
    response_model=ActiveDownloadItem,
)
async def get_active_download_by_guid_prowlarr(
    guid_prowlarr: str,
    query: GetActiveDownloadByGuidProwlarrQuery = Depends(
        create_get_active_download_by_guid_prowlarr_query
    ),
):
    """Get torrent download by Prowlarr GUID."""
    row = await query.execute(guid_prowlarr)
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Torrent download for guid_prowlarr {guid_prowlarr} not found",
        )
    return to_active_download_item(row)


@tracking_routes.get("/active-downloads/{download_id}", response_model=ActiveDownloadItem)
async def get_active_download(
    download_id: int,
    query: GetActiveDownloadByIdQuery = Depends(create_get_active_download_by_id_query),
):
    """Get one torrent download row by id."""
    row = await query.execute(download_id)
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Torrent download {download_id} not found",
        )
    return to_active_download_item(row)


@tracking_routes.get(
    "/deferred-downloads",
    response_model=DeferredDownloadListResponse,
    summary="List torrents waiting for download volume space",
)
async def list_deferred_downloads(
    limit: int = Query(100, ge=1, le=500),
    query: ListDeferredDownloadsQuery = Depends(
        create_list_deferred_downloads_query
    ),
):
    """
    Prowlarr/Deluge sends are postponed here when the quarantine/download volume is full.

    Magnets are kept via ``guid_prowlarr`` + ``indexer_id``; released automatically when space is available.
    """
    rows = await query.execute(limit=limit)
    items = [
        DeferredDownloadItem(
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
    return DeferredDownloadListResponse(
        items=items,
        total=len(items),
        download_volume_path=settings.container_deluge_quarantine_path,
    )


@tracking_routes.post(
    "/deferred-downloads/process",
    response_model=ProcessDeferredDownloadsResponse,
    summary="Process deferred torrents when download volume has space",
)
async def process_deferred_downloads(
    limit: int = Query(20, ge=1, le=100, description="Max pending rows to try"),
    use_case: ProcessDeferredDownloadsUseCase = Depends(
        create_process_deferred_downloads_use_case
    ),
):
    """
    Manually drain the deferred queue (same logic as the scheduler).

    Sends magnets to Prowlarr/Deluge when the quarantine volume has enough free space.
    """
    result = await use_case.execute(limit=limit)
    return ProcessDeferredDownloadsResponse(
        checked=result.checked,
        sent=result.sent,
        still_pending=result.still_pending,
        failed=result.failed,
    )
