"""HTTP routes for Prowlarr torrent search."""
from fastapi import APIRouter, Depends, HTTPException, status
from app.application.prowlarr.useCases.downloadTorrent import DownloadTorrentUseCase
from app.application.prowlarr.queries.findBestTorrent import GetBestTorrentsQuery
from app.application.prowlarr.queries.testProwlarrConnection import (
    TestProwlarrConnectionQuery,
    GetProwlarrIndexerCountQuery,
)
from app.factories.prowlarr.prowlarrFactory import (
    createFindBestTorrentQuery,
    createDownloadTorrentUseCase,
    createTestProwlarrConnectionQuery,
    createGetProwlarrIndexerCountQuery,
)
from app.adapters.http.schemas.prowlarr import (
    SearchByQueryRequest,
    SearchResponse,
    ProwlarrConnectionResponse,
    ProwlarrIndexerCountResponse,
)
import logging

logger = logging.getLogger(__name__)

prowlarrRoutes = APIRouter(prefix="/prowlarr", tags=["prowlarr"])


@prowlarrRoutes.post("/search/by-query", response_model=SearchResponse)
async def search_torrents_by_query(
    request: SearchByQueryRequest,
    find_query: GetBestTorrentsQuery = Depends(createFindBestTorrentQuery),
    download_use_case: DownloadTorrentUseCase = Depends(createDownloadTorrentUseCase),
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
        
        # 1. Find best torrents (ordered by score)
        results = await find_query.execute(
            query=request.query,
            media_type=request.media_type,
        )
        
        # Return 404 if no results found
        if not results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No torrents found matching query: '{request.query}'"
            )
        
        # Get the best result (first in the ordered list)
        best_result = results[0]
        
        # 2. Optionally download torrent
        if request.auto_add_to_deluge:
            await download_use_case.execute(best_result)
        
        
        # Return 200 OK with results
        return SearchResponse(
            title=best_result.title,
            indexer=best_result.indexer,
            size_gb=best_result.size,
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
    query: TestProwlarrConnectionQuery = Depends(createTestProwlarrConnectionQuery),
):
    """
    Test connection to Prowlarr.
    
    Returns:
        ProwlarrConnectionResponse with connection status and version
    """
    status = await query.execute()
    return ProwlarrConnectionResponse(
        connected=status.connected,
        status="healthy" if status.is_healthy else "unhealthy",
        version=status.version,
        error=status.error,
    )


@prowlarrRoutes.get("/indexers/count", response_model=ProwlarrIndexerCountResponse)
async def get_prowlarr_indexer_count(
    query: GetProwlarrIndexerCountQuery = Depends(createGetProwlarrIndexerCountQuery),
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

