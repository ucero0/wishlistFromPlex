from fastapi import APIRouter, Depends, HTTPException
from app.factories.plex.plexServerFactory import createIsItemInLibraryQuery
from app.adapters.http.schemas.plex.plexServerSchemas import IsItemInLibraryRequest, IsItemInLibraryResponse
from app.domain.models.media import MediaItem
from app.application.plex.queries.getPlexServerItem import IsItemInLibraryQuery
from app.adapters.http.security.dependencies import APIKey
import logging

logger = logging.getLogger(__name__)

plexServerRoutes = APIRouter(prefix="/servers", tags=["plex-servers"])

@plexServerRoutes.post("/isItemInLibrary", response_model=IsItemInLibraryResponse)
async def isItemInLibrary(
    request: IsItemInLibraryRequest, query: IsItemInLibraryQuery = Depends(createIsItemInLibraryQuery)
):
    logger.info(f"Received isItemInLibrary request: guid={request.guid}, type={request.type}, userToken={request.userToken[:4]}***")
    try:
        media_item = MediaItem(guid=request.guid, type=request.type)
        logger.debug(f"Created MediaItem: {media_item}")
        has_media = await query.execute(request.userToken, media_item)
        logger.info(f"Query result: has_media={has_media}")
        return IsItemInLibraryResponse(has_media=has_media)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error checking if item is in library: {type(e).__name__}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))