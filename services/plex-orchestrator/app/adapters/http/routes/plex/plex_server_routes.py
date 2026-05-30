import logging

from fastapi import APIRouter, Depends, Query

from app.adapters.http.schemas.plex.plex_server_schemas import (
    GetPlexLibraryLocationsResponse,
    IsItemInLibraryResponse,
    SyncPlexLibraryLocationsResponse,
)
from app.application.plex.queries.get_plex_library_locations_query import (
    GetPlexLibraryLocationsByMediaQuery,
)
from app.application.plex.queries.get_plex_server_item_query import IsItemInLibraryQuery
from app.application.plex.use_cases.sync_plex_library_paths_use_case import (
    SyncPlexLibraryPathsFromServerUseCase,
)
from app.domain.models.media import MediaItem, MediaType
from app.factories.plex.plex_library_path_factory import (
    create_sync_plex_library_paths_use_case,
)
from app.factories.plex.plex_server_factory import (
    create_get_plex_library_locations_by_media_query,
    create_is_item_in_library_query,
)

logger = logging.getLogger(__name__)

plex_server_routes = APIRouter(prefix="/servers", tags=["plex-servers"])


@plex_server_routes.get("/items/in-library", response_model=IsItemInLibraryResponse)
async def is_item_in_library(
    guid: str = Query(..., description="Plex media GUID"),
    media_type: MediaType = Query(
        ...,
        alias="type",
        description="Media type (movie, show, …)",
    ),
    query: IsItemInLibraryQuery = Depends(create_is_item_in_library_query),
):
    """Check whether a GUID exists in the Plex library (server admin token)."""
    logger.info("is_item_in_library guid=%s type=%s", guid, media_type)
    media_item = MediaItem(guid=guid, type=media_type)
    has_media = await query.execute(media_item)
    return IsItemInLibraryResponse(has_media=has_media)


@plex_server_routes.get(
    "/library/locations-by-media",
    response_model=GetPlexLibraryLocationsResponse,
)
async def get_library_locations_by_media(
    query: GetPlexLibraryLocationsByMediaQuery = Depends(
        create_get_plex_library_locations_by_media_query
    ),
):
    """Library sections with root paths from Plex Server API (server admin token)."""
    result = await query.execute()
    return GetPlexLibraryLocationsResponse.model_validate(result.model_dump())


@plex_server_routes.post(
    "/library/locations-by-media/sync",
    response_model=SyncPlexLibraryLocationsResponse,
)
async def sync_library_locations_by_media(
    use_case: SyncPlexLibraryPathsFromServerUseCase = Depends(
        create_sync_plex_library_paths_use_case
    ),
):
    """
    Same data as GET ``/library/locations-by-media``, persisted to the database.

    Run after adding or changing library folders in Plex. For stored paths and disk
    stats, use ``GET /plex/library-paths`` and related routes.
    """
    result = await use_case.execute()
    layout = GetPlexLibraryLocationsResponse.model_validate(
        result["sections"].model_dump()
    )
    return SyncPlexLibraryLocationsResponse(
        sections=layout.sections,
        synced_from_server=result["synced_from_server"],
        active_in_database=result["active_in_database"],
    )


from app.adapters.http.routes.plex.plex_server_admin_token_routes import (
    plex_server_admin_token_routes,
)

plex_server_routes.include_router(plex_server_admin_token_routes)
