import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Query

from app.adapters.http.mappers.plex_disk_http_mapper import (
    sections_disk_usage_to_http_bodies,
)
from app.adapters.http.schemas.plex.plexServerSchemas import (
    PLEX_USER_TOKEN_HEADER,
    GetPlexLibraryLocationsDiskUsageResponse,
    GetPlexLibraryLocationsResponse,
    IsItemInLibraryResponse,
    SyncPlexLibraryLocationsResponse,
)
from app.application.plex.queries.listPlexLibraryPaths import ListPlexLibraryPathsFromDbQuery
from app.application.plex.useCases.syncPlexLibraryPaths import (
    SyncPlexLibraryPathsFromServerUseCase,
)
from app.factories.plex.plexLibraryPathFactory import (
    create_list_plex_library_paths_from_db_query,
    create_sync_plex_library_paths_use_case,
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
    """Library sections with root paths from Plex Server API (movie, tvshow, other)."""
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


@plexServerRoutes.post(
    "/library/locations-by-media/sync",
    response_model=SyncPlexLibraryLocationsResponse,
)
async def sync_library_locations_by_media(
    user_token: str = Header(
        ...,
        alias=PLEX_USER_TOKEN_HEADER,
        description="Plex user token",
    ),
    use_case: SyncPlexLibraryPathsFromServerUseCase = Depends(
        create_sync_plex_library_paths_use_case
    ),
):
    """
    Same data as GET ``/library/locations-by-media``, persisted to the database.

    Run after adding or changing library folders in Plex. Ingest uses DB paths
    to pick a destination with enough free space.
    """
    try:
        result = await use_case.execute(user_token)
        layout = GetPlexLibraryLocationsResponse.model_validate(
            result["sections"].model_dump()
        )
        return SyncPlexLibraryLocationsResponse(
            sections=layout.sections,
            synced_from_server=result["synced_from_server"],
            active_in_database=result["active_in_database"],
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error syncing Plex library locations: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e


@plexServerRoutes.get(
    "/library/locations-by-media/stored",
    response_model=GetPlexLibraryLocationsResponse,
    deprecated=True,
    summary="[Legacy] Stored library paths — prefer GET /plex/library-paths",
)
async def get_stored_library_locations_by_media(
    active_only: bool = Query(True, description="Only paths marked active in DB"),
    query: ListPlexLibraryPathsFromDbQuery = Depends(
        create_list_plex_library_paths_from_db_query
    ),
):
    """Library paths last synced from Plex (database copy, same response shape as live GET)."""
    try:
        result = await query.execute(active_only=active_only)
        return GetPlexLibraryLocationsResponse.model_validate(result.model_dump())
    except Exception as e:
        logger.exception("Error listing stored Plex library locations: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e


@plexServerRoutes.get(
    "/library/locations-by-media/disk-usage",
    response_model=GetPlexLibraryLocationsDiskUsageResponse,
    deprecated=True,
    summary="[Legacy] Live Plex disk usage — prefer GET /plex/library-paths/media-devices",
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
    **Legacy:** prefer ``GET /plex/library-paths/media-devices`` (DB snapshot, syncs from Plex).

    Plex movie/TV library paths plus volume root and used/free/total space (live Plex + host probe).

    Sizes are human-readable (e.g. ``879.42 GB``). Disk stats are computed on **this**
    machine (the FastAPI process). If Plex reports paths not visible here, those entries
    include ``error`` and null sizes.
    """
    logger.info(
        "get_library_locations_disk_usage %s present=%s",
        PLEX_USER_TOKEN_HEADER,
        bool(user_token),
    )
    try:
        result = await query.execute(user_token)
        return GetPlexLibraryLocationsDiskUsageResponse(
            sections=sections_disk_usage_to_http_bodies(result.sections),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            "Error fetching Plex library disk usage: %s: %s",
            type(e).__name__,
            str(e),
        )
        raise HTTPException(status_code=500, detail=str(e)) from e
