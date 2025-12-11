"""Torrent search module API routes."""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import get_api_key
from app.modules.torrent_search.service import TorrentSearchService
from app.modules.torrent_search.schemas import (
    SearchRequest,
    SearchByQueryRequest,
    SearchResponse,
    SearchResultResponse,
    SearchStatsResponse,
    SearchStatusEnum,
    TorrentResult,
    ProwlarrStatusResponse,
)
from app.modules.torrent_search.models import SearchStatus, TorrentSearchResult

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/torrent-search", tags=["torrent-search"])


@router.get("/prowlarr/status", response_model=ProwlarrStatusResponse, dependencies=[Depends(get_api_key)])
async def get_prowlarr_status(db: Session = Depends(get_db)):
    """
    Check Prowlarr connection status.
    
    Returns connection status, version, and number of configured indexers.
    """
    service = TorrentSearchService(db)
    
    connected, version, error = await service.test_connection()
    indexer_count = 0
    
    if connected:
        indexer_count = await service.get_indexer_count()
    
    return ProwlarrStatusResponse(
        connected=connected,
        version=version,
        indexer_count=indexer_count,
        error=error
    )


@router.post("/search-by-query", dependencies=[Depends(get_api_key)])
async def search_torrent_by_query(request: SearchByQueryRequest, db: Session = Depends(get_db)):
    """
    Search for torrents using a query string (independent of wishlist items).
    
    This is the reusable search endpoint that works independently.
    The orchestration service uses this to coordinate searches.
    
    This endpoint:
    1. Searches Prowlarr with the provided query
    2. Scores results by quality (TrueHD audio, 2160p resolution prioritized)
    3. Optionally auto-adds the best match to Deluge
    
    Quality scoring priority:
    - TrueHD/DTS-HD MA audio: Highest
    - 2160p/4K resolution: High
    - HDR/Dolby Vision: Medium
    - Remux/BluRay source: Medium
    - Seeders (health): Low
    """
    service = TorrentSearchService(db)
    
    try:
        result = await service.search_by_query(
            query=request.query,
            media_type=request.media_type,
            auto_add_to_deluge=request.auto_add_to_deluge,

        )
        if not result:
            return []
        return result
        
        
    except Exception as e:
        logger.exception(f"Error searching for query '{request.query}'")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )

