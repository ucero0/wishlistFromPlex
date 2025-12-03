"""Deluge module API routes."""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import get_api_key
from app.modules.deluge.models import TorrentItem, TorrentStatus
from app.modules.deluge.schemas import (
    AddTorrentRequest,
    AddTorrentResponse,
    RemoveTorrentRequest,
    RemoveTorrentResponse,
    TorrentItemResponse,
    TorrentInfoResponse,
    TorrentListResponse,
    DelugeStatusResponse,
)
from app.modules.deluge import service
from app.modules.deluge.constants import MODULE_PREFIX

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix=MODULE_PREFIX, tags=[MODULE_PREFIX.strip("/")])


# =============================================================================
# Status Endpoints
# =============================================================================

@router.get("/status", response_model=DelugeStatusResponse)
async def get_deluge_status():
    """
    Check Deluge daemon connection status.
    
    No authentication required - useful for health checks.
    """
    connected, version, error = service.test_connection()
    return DelugeStatusResponse(
        connected=connected,
        daemon_version=version,
        error=error
    )


# =============================================================================
# Torrent Management Endpoints
# =============================================================================

@router.post("/torrents", response_model=AddTorrentResponse, dependencies=[Depends(get_api_key)])
async def add_torrent(
    request: AddTorrentRequest,
    db: Session = Depends(get_db)
):
    """
    Add a torrent to Deluge via magnet link.
    
    Associates the torrent with a Plex rating_key for tracking.
    Multiple torrents with the same rating_key are allowed (different formats).
    
    Requires API key authentication.
    """
    # Extract hash from magnet link to check for duplicates
    import re
    hash_match = re.search(r'btih:([a-fA-F0-9]{40})', request.magnet_link)
    if hash_match:
        magnet_hash = hash_match.group(1).lower()
        existing = db.query(TorrentItem).filter(
            TorrentItem.torrent_hash == magnet_hash,
            TorrentItem.status.notin_([TorrentStatus.REMOVED])
        ).first()
        
        if existing:
            return AddTorrentResponse(
                success=False,
                message=f"Torrent with hash {magnet_hash} already exists",
                torrent_hash=existing.torrent_hash,
                torrent=TorrentItemResponse.model_validate(existing)
            )
    
    success, result, torrent_item = service.add_magnet(
        request.magnet_link,
        request.rating_key,
        db
    )
    
    if success and torrent_item:
        return AddTorrentResponse(
            success=True,
            message="Torrent added successfully",
            torrent_hash=result,
            torrent=TorrentItemResponse.model_validate(torrent_item)
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add torrent: {result}"
        )


@router.get("/torrents", response_model=TorrentListResponse)
async def list_torrents(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    List all tracked torrents with optional filtering.
    
    No authentication required.
    """
    torrent_status = None
    if status_filter:
        try:
            torrent_status = TorrentStatus(status_filter.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status_filter}. Valid values: {[s.value for s in TorrentStatus]}"
            )
    
    torrents, total = service.get_all_tracked_torrents(db, torrent_status, limit, offset)
    
    return TorrentListResponse(
        total=total,
        torrents=[TorrentItemResponse.model_validate(t) for t in torrents]
    )


@router.get("/torrents/by-rating-key/{rating_key}", response_model=TorrentListResponse)
async def get_torrents_by_rating_key(
    rating_key: str,
    db: Session = Depends(get_db)
):
    """
    Get all torrents associated with a Plex rating_key.
    
    No authentication required.
    """
    torrents = service.get_torrents_by_rating_key(rating_key, db)
    
    return TorrentListResponse(
        total=len(torrents),
        torrents=[TorrentItemResponse.model_validate(t) for t in torrents]
    )


@router.get("/torrents/{torrent_hash}", response_model=TorrentItemResponse)
async def get_torrent(
    torrent_hash: str,
    db: Session = Depends(get_db)
):
    """
    Get a specific torrent by its hash.
    
    No authentication required.
    """
    torrent = service.get_torrent_by_hash(torrent_hash, db)
    
    if not torrent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Torrent {torrent_hash} not found"
        )
    
    return TorrentItemResponse.model_validate(torrent)


@router.get("/torrents/{torrent_hash}/info", response_model=TorrentInfoResponse)
async def get_torrent_info(torrent_hash: str):
    """
    Get live torrent info directly from Deluge daemon.
    
    No authentication required.
    """
    info = service.extract_torrent_data(torrent_hash)
    
    if not info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Torrent {torrent_hash} not found in Deluge daemon"
        )
    
    return info


@router.delete("/torrents/{torrent_hash}", response_model=RemoveTorrentResponse, dependencies=[Depends(get_api_key)])
async def remove_torrent(
    torrent_hash: str,
    remove_data: bool = Query(False, description="Also delete downloaded files"),
    db: Session = Depends(get_db)
):
    """
    Remove a torrent from Deluge by its hash.
    
    - `remove_data=false`: Remove torrent only, keep downloaded files
    - `remove_data=true`: Remove torrent AND delete all downloaded files
    
    Requires API key authentication.
    """
    # Check if torrent exists in our database
    torrent = service.get_torrent_by_hash(torrent_hash, db)
    if not torrent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Torrent {torrent_hash} not found in database"
        )
    
    success, message = service.remove_torrent(torrent_hash, remove_data, db)
    
    if success:
        return RemoveTorrentResponse(
            success=True,
            message=message,
            torrent_hash=torrent_hash,
            data_removed=remove_data
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=message
        )


@router.delete("/torrents/by-rating-key/{rating_key}", response_model=RemoveTorrentResponse, dependencies=[Depends(get_api_key)])
async def remove_torrents_by_rating_key(
    rating_key: str,
    remove_data: bool = Query(False, description="Also delete downloaded files"),
    db: Session = Depends(get_db)
):
    """
    Remove all torrents associated with a Plex rating_key.
    
    - `remove_data=false`: Remove torrents only, keep downloaded files
    - `remove_data=true`: Remove torrents AND delete all downloaded files
    
    Requires API key authentication.
    """
    success, message, removed_hashes = service.remove_torrent_by_rating_key(rating_key, remove_data, db)
    
    if success:
        return RemoveTorrentResponse(
            success=True,
            message=message,
            torrent_hash=",".join(removed_hashes) if removed_hashes else "",
            data_removed=remove_data
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND if "not found" in message.lower() else status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=message
        )


# =============================================================================
# Sync Endpoint
# =============================================================================

@router.post("/sync", dependencies=[Depends(get_api_key)])
async def sync_torrents(db: Session = Depends(get_db)):
    """
    Sync all tracked torrents with Deluge daemon status.
    
    Updates progress, speed, status etc. for all active torrents.
    
    Requires API key authentication.
    """
    synced, errors = service.sync_torrent_status(db)
    
    return {
        "message": "Sync completed",
        "synced_count": synced,
        "error_count": errors
    }


# =============================================================================
# Daemon Info Endpoints
# =============================================================================

@router.get("/daemon/torrents", response_model=list[TorrentInfoResponse])
async def get_all_daemon_torrents():
    """
    Get all torrents directly from Deluge daemon.
    
    Returns live data, not from database.
    No authentication required.
    """
    return service.get_all_torrents_info()

