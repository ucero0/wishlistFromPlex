import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Query

from app.adapters.http.schemas.plex.plexServerSchemas import (
    PLEX_USER_TOKEN_HEADER,
    GetPlexLibraryLocationsDiskUsageResponse,
    GetPlexLibraryLocationsResponse,
    IsItemInLibraryResponse,
)
from app.application.plex.queries.getPlexLibraryLocations import GetPlexLibraryLocationsByMediaQuery
from app.application.plex.queries.getPlexLibraryLocationsDiskUsage import (
    GetPlexLibraryLocationsDiskUsageQuery,
)
from app.application.plex.queries.getPlexServerItem import IsItemInLibraryQuery
from app.domain.models.media import MediaItem, MediaType
from app.factories.plex.plexServerFactory import (
    createGetPlexLibraryLocationsByMediaQuery,
    createGetPlexLibraryLocationsDiskUsageQuery,
    createIsItemInLibraryQuery,
)

logger = logging.getLogger(__name__)

plexServerRoutes = APIRouter(prefix="/servers", tags=["plex-servers"])


@plexServerRoutes.get("/items/in-library", response_model=IsItemInLibraryResponse)
async def is_item_in_library(
    guid: str = Query(..., description="Plex media GUID"),
    media_type: MediaType = Query(
        ...,
        alias="type",
        description="Media type (movie, show, …)",
    ),
    user_token: str = Header(
        ...,
        alias=PLEX_USER_TOKEN_HEADER,
        description="Plex user token (same as Plex uses for authenticated API calls)",
    ),
    query: IsItemInLibraryQuery = Depends(createIsItemInLibraryQuery),
):
    """Check whether a GUID exists in the Plex library (read-only)."""
    logger.info(
        "is_item_in_library guid=%s type=%s token_prefix=%s***",
        guid,
        media_type,
        user_token[:4] if len(user_token) >= 4 else "****",
    )
    try:
        media_item = MediaItem(guid=guid, type=media_type)
        has_media = await query.execute(user_token, media_item)
        return IsItemInLibraryResponse(has_media=has_media)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            "Error checking if item is in library: %s: %s",
            type(e).__name__,
            str(e),
        )
        raise HTTPException(status_code=500, detail=str(e)) from e


@plexServerRoutes.get(
    "/library/locations-by-media",
    response_model=GetPlexLibraryLocationsResponse,
)
async def get_library_locations_by_media(
    user_token: str = Header(
        ...,
        alias=PLEX_USER_TOKEN_HEADER,
        description="Plex user token",
    ),
    query: GetPlexLibraryLocationsByMediaQuery = Depends(
        createGetPlexLibraryLocationsByMediaQuery
    ),
):
    """Movie and TV library sections with configured root paths (read-only)."""
    logger.info(
        "get_library_locations_by_media %s present=%s",
        PLEX_USER_TOKEN_HEADER,
        bool(user_token),
    )
    try:
        result = await query.execute(user_token)
        return GetPlexLibraryLocationsResponse.model_validate(result.model_dump())
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            "Error fetching Plex library locations: %s: %s",
            type(e).__name__,
            str(e),
        )
        raise HTTPException(status_code=500, detail=str(e)) from e


@plexServerRoutes.get(
    "/library/locations-by-media/disk-usage",
    response_model=GetPlexLibraryLocationsDiskUsageResponse,
)
async def get_library_locations_disk_usage(
    user_token: str = Header(
        ...,
        alias=PLEX_USER_TOKEN_HEADER,
        description="Plex user token",
    ),
    query: GetPlexLibraryLocationsDiskUsageQuery = Depends(
        createGetPlexLibraryLocationsDiskUsageQuery
    ),
):
    """
    Plex movie/TV library paths plus volume root and used/free/total bytes (read-only).

    Disk stats are computed on **this** machine (the FastAPI process). If Plex reports
    paths that are not visible here (e.g. host-only paths in Docker), those entries
    include ``error`` and null stats.
    """
    logger.info(
        "get_library_locations_disk_usage %s present=%s",
        PLEX_USER_TOKEN_HEADER,
        bool(user_token),
    )
    try:
        result = await query.execute(user_token)
        return GetPlexLibraryLocationsDiskUsageResponse.model_validate(result.model_dump())
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            "Error fetching Plex library disk usage: %s: %s",
            type(e).__name__,
            str(e),
        )
        raise HTTPException(status_code=500, detail=str(e)) from e
