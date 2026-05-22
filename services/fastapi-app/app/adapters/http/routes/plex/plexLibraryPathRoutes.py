"""Read-only API for Plex library paths and media HDD volumes stored in the database."""

import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Query

from app.adapters.http.mappers.plex_disk_http_mapper import (
    media_device_to_http_body,
    path_row_to_http_item,
    refresh_meta_to_serve_body,
    sections_disk_usage_to_http_bodies,
)
from app.adapters.http.schemas.plex.plexLibraryPathSchemas import (
    PlexLibraryPathListResponse,
    PlexLibraryPathsDiskUsageResponse,
    PlexMediaHddDevicesResponse,
)
from app.adapters.http.schemas.plex.plexServerSchemas import PLEX_USER_TOKEN_HEADER
from app.application.plex.queries.getPlexLibraryMediaDevicesFromDb import (
    GetPlexLibraryMediaDevicesFromDbQuery,
)
from app.application.plex.queries.getPlexLibraryPathsDiskUsageFromDb import (
    GetPlexLibraryPathsDiskUsageFromDbQuery,
)
from app.application.plex.queries.listPlexLibraryPathsFlat import (
    ListPlexLibraryPathsFlatQuery,
)
from app.application.plex.useCases.refreshPlexLibraryPathsBeforeServe import (
    RefreshPlexLibraryPathsBeforeServeUseCase,
)
from app.factories.plex.plexLibraryPathFactory import (
    create_get_plex_library_media_devices_from_db_query,
    create_get_plex_library_paths_disk_usage_from_db_query,
    create_list_plex_library_paths_flat_query,
    create_refresh_plex_library_paths_before_serve_use_case,
)

logger = logging.getLogger(__name__)

PLEX_MEDIA_STORAGE_TAG = "Plex Media HDD (DB)"

plexLibraryPathRoutes = APIRouter(tags=[PLEX_MEDIA_STORAGE_TAG])


@plexLibraryPathRoutes.get(
    "/library-paths",
    response_model=PlexLibraryPathListResponse,
    operation_id="list_plex_library_paths_db",
    summary="List Plex library paths (database)",
)
async def list_plex_library_paths(
    active_only: bool = Query(
        True, description="Only paths marked active (still present in Plex)"
    ),
    media_type: str | None = Query(
        None, description="Filter by media type: movie, tvshow, other"
    ),
    user_token: str | None = Header(
        None,
        alias=PLEX_USER_TOKEN_HEADER,
        description="Optional Plex token to refresh paths from server before read",
    ),
    refresh: RefreshPlexLibraryPathsBeforeServeUseCase = Depends(
        create_refresh_plex_library_paths_before_serve_use_case
    ),
    query: ListPlexLibraryPathsFlatQuery = Depends(
        create_list_plex_library_paths_flat_query
    ),
):
    """
    Flat rows from ``plex_library_paths`` with human-readable disk sizes.

    Refreshes from Plex when a token is sent (header or first active DB user).
    On Plex failure, returns the last stored snapshot.
    """
    try:
        meta = await refresh.execute(user_token=user_token, active_only=active_only)
        rows = await query.execute(active_only=active_only)
        if media_type:
            rows = [r for r in rows if r.media_type == media_type]
        items = [path_row_to_http_item(r) for r in rows]
        serve_meta = refresh_meta_to_serve_body(meta)
        return PlexLibraryPathListResponse(
            items=items,
            total=len(items),
            **serve_meta.model_dump(),
        )
    except Exception as e:
        logger.exception("Error listing Plex library paths: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e


@plexLibraryPathRoutes.get(
    "/library-paths/disk-usage",
    response_model=PlexLibraryPathsDiskUsageResponse,
    operation_id="get_plex_library_paths_disk_usage_db",
    summary="Library paths disk usage by section (database)",
)
async def get_plex_library_paths_disk_usage_from_db(
    active_only: bool = Query(True, description="Only paths marked active in the DB"),
    user_token: str | None = Header(None, alias=PLEX_USER_TOKEN_HEADER),
    refresh: RefreshPlexLibraryPathsBeforeServeUseCase = Depends(
        create_refresh_plex_library_paths_before_serve_use_case
    ),
    query: GetPlexLibraryPathsDiskUsageFromDbQuery = Depends(
        create_get_plex_library_paths_disk_usage_from_db_query
    ),
):
    """
    Plex library sections with per-folder ``total`` / ``used`` / ``free`` labels (e.g. ``879 GB``).

    Syncs from Plex and re-measures disk space before responding.
    """
    try:
        meta = await refresh.execute(user_token=user_token, active_only=active_only)
        result = await query.execute(active_only=active_only)
        serve_meta = refresh_meta_to_serve_body(meta)
        return PlexLibraryPathsDiskUsageResponse(
            sections=sections_disk_usage_to_http_bodies(result.sections),
            **serve_meta.model_dump(),
        )
    except Exception as e:
        logger.exception("Error fetching DB library path disk usage: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e


@plexLibraryPathRoutes.get(
    "/library-paths/media-devices",
    response_model=PlexMediaHddDevicesResponse,
    operation_id="list_plex_media_hdd_devices_db",
    summary="List media HDD volumes (database)",
)
async def list_plex_media_hdd_devices_from_db(
    active_only: bool = Query(True, description="Only paths marked active in the DB"),
    user_token: str | None = Header(None, alias=PLEX_USER_TOKEN_HEADER),
    refresh: RefreshPlexLibraryPathsBeforeServeUseCase = Depends(
        create_refresh_plex_library_paths_before_serve_use_case
    ),
    query: GetPlexLibraryMediaDevicesFromDbQuery = Depends(
        create_get_plex_library_media_devices_from_db_query
    ),
):
    """
    **Primary DB HDD endpoint:** unique volumes (``volume_root``) with ``total`` / ``used`` / ``free``,
    ``used_percent``, and which Plex library folders sit on each drive.

    Syncs from Plex first; if Plex is unreachable, returns the last snapshot still in the DB.
    """
    try:
        meta = await refresh.execute(user_token=user_token, active_only=active_only)
        result = await query.execute(active_only=active_only)
        serve_meta = refresh_meta_to_serve_body(meta)
        return PlexMediaHddDevicesResponse(
            devices=[media_device_to_http_body(d) for d in result.devices],
            total=result.total,
            **serve_meta.model_dump(),
        )
    except Exception as e:
        logger.exception("Error listing DB media HDD devices: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e
