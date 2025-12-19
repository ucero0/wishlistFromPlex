"""HTTP routes for Prowlarr torrent search."""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional
from app.application.prowlarr.useCases.downloadTorrent import DownloadTorrentUseCase
from app.application.prowlarr.queries.findBestTorrent import FindBestTorrentQuery
from app.application.prowlarr.queries.testProwlarrConnection import (
    TestProwlarrConnectionQuery,
    GetProwlarrIndexerCountQuery,
)
from app.factories.prowlarr.prowlarrFactory import (
    create_find_best_torrent_query,
    create_download_torrent_use_case,
    create_test_prowlarr_connection_query,
    create_get_prowlarr_indexer_count_query,
)
from app.adapters.http.schemas.prowlarr import (
    SearchByQueryRequest,
    SearchResponse,
    ProwlarrConnectionResponse,
    ProwlarrIndexerCountResponse,
)
from app.domain.models.torrent_search import SearchStatusEnum, TorrentSearchResult
import logging

logger = logging.getLogger(__name__)

prowlarrRoutes = APIRouter(prefix="/prowlarr", tags=["prowlarr"])


@prowlarrRoutes.post("/search/by-query", response_model=SearchResponse)
async def search_torrents_by_query(
    request: SearchByQueryRequest,
    find_query: FindBestTorrentQuery = Depends(create_find_best_torrent_query),
    download_use_case: DownloadTorrentUseCase = Depends(create_download_torrent_use_case),
):
    """
    Search for torrents using a query string.
    
    Args:
        request: Search request with query, media_type, and options
        find_query: Find best torrent query dependency
        download_use_case: Download torrent use case dependency
        
    Returns:
        SearchResponse with best match and status (200 OK)
        
    Raises:
        HTTPException 404: When no torrents are found matching the query
    """
    try:
        logger.info(f"Search request: query='{request.query}', media_type={request.media_type}")
        
        # 1. Find best torrent
        best_result = await find_query.execute(
            query=request.query,
            media_type=request.media_type,
        )
        
        # Return 404 if no results found
        if not best_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No torrents found matching query: '{request.query}'"
            )
        
        # 2. Optionally download torrent
        download_success = True
        if request.auto_add_to_deluge:
            download_success = await download_use_case.execute(best_result)
        
        
        # Return 200 OK with results
        return SearchResponse(
            title=best_result.title,
            indexer=best_result.indexer,
            sizeGb=best_result.size,
            seeders=best_result.seeders,
            leechers=best_result.leechers,
 
        )
            
    except HTTPException:
        # Re-raise HTTP exceptions (like 404)
        raise
    except Exception as e:
        logger.exception(f"Error searching torrents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching torrents: {str(e)}"
        )


@prowlarrRoutes.get("/test-connection", response_model=ProwlarrConnectionResponse)
async def test_prowlarr_connection(
    query: TestProwlarrConnectionQuery = Depends(create_test_prowlarr_connection_query),
):
    """
    Test connection to Prowlarr.
    
    Returns:
        ProwlarrConnectionResponse with connection status and version
    """
    try:
        connected, version, error = await query.execute()
        return ProwlarrConnectionResponse(
            connected=connected,
            version=version,
            error=error,
        )
    except Exception as e:
        logger.exception(f"Error testing Prowlarr connection: {e}")
        return ProwlarrConnectionResponse(
            connected=False,
            version=None,
            error=str(e),
        )


@prowlarrRoutes.get("/indexers/count", response_model=ProwlarrIndexerCountResponse)
async def get_prowlarr_indexer_count(
    query: GetProwlarrIndexerCountQuery = Depends(create_get_prowlarr_indexer_count_query),
):
    """
    Get the number of configured indexers in Prowlarr.
    
    Returns:
        ProwlarrIndexerCountResponse with the count of enabled indexers
    """
    try:
        count = await query.execute()
        return ProwlarrIndexerCountResponse(count=count)
    except Exception as e:
        logger.exception(f"Error getting indexer count: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting indexer count: {str(e)}"
        )

