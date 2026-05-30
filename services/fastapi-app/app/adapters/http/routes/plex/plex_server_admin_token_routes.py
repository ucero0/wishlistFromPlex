"""Manage Plex Media Server admin token (library API credential)."""
from fastapi import APIRouter, Depends, HTTPException, status

from app.adapters.http.schemas.plex.plex_server_admin_token_schemas import (
    PlexServerAdminTokenStatusResponse,
    SetPlexServerAdminTokenRequest,
    UpsertPlexServerAdminTokenResponse,
)
from app.application.plex.queries.get_plex_server_admin_token_config_query import (
    GetPlexServerAdminTokenConfigQuery,
)
from app.application.plex.use_cases.upsert_plex_server_admin_token_use_case import (
    UpsertPlexServerAdminTokenUseCase,
)
from app.factories.plex.plex_server_config_factory import (
    create_get_plex_server_admin_token_config_query,
    create_upsert_plex_server_admin_token_use_case,
)

plex_server_admin_token_routes = APIRouter(tags=["plex-servers"])


@plex_server_admin_token_routes.get(
    "/admin-token",
    response_model=PlexServerAdminTokenStatusResponse,
    summary="Get Plex server admin token status",
)
async def get_plex_server_admin_token_status(
    query: GetPlexServerAdminTokenConfigQuery = Depends(
        create_get_plex_server_admin_token_config_query
    ),
):
    """
    Returns whether a server admin token is configured and where it comes from.

    Resolution order at runtime: **database** row overrides **environment** (``.env``).
    """
    status_info = await query.execute()
    return PlexServerAdminTokenStatusResponse(
        configured=status_info.configured,
        source=status_info.source,
        token_masked=status_info.token_masked,
        updated_at=status_info.updated_at,
    )


async def _upsert_admin_token(
    request: SetPlexServerAdminTokenRequest,
    use_case: UpsertPlexServerAdminTokenUseCase,
) -> UpsertPlexServerAdminTokenResponse:
    config, token_masked, created = await use_case.execute(request.admin_token)
    return UpsertPlexServerAdminTokenResponse(
        token_masked=token_masked,
        updated_at=config.updated_at,
        created=created,
    )


@plex_server_admin_token_routes.post(
    "/admin-token",
    response_model=UpsertPlexServerAdminTokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Plex server admin token in database",
)
async def create_plex_server_admin_token(
    request: SetPlexServerAdminTokenRequest,
    use_case: UpsertPlexServerAdminTokenUseCase = Depends(
        create_upsert_plex_server_admin_token_use_case
    ),
    query: GetPlexServerAdminTokenConfigQuery = Depends(
        create_get_plex_server_admin_token_config_query
    ),
):
    """
    Save the admin token to the database after validating it against Plex.

    Returns **409** if a token is already stored in the database (use PUT to update).
    """
    current = await query.execute()
    if current.source == "database":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Plex server admin token already exists in database. Use PUT to update.",
        )
    return await _upsert_admin_token(request, use_case)


@plex_server_admin_token_routes.put(
    "/admin-token",
    response_model=UpsertPlexServerAdminTokenResponse,
    summary="Update Plex server admin token in database",
)
async def update_plex_server_admin_token(
    request: SetPlexServerAdminTokenRequest,
    use_case: UpsertPlexServerAdminTokenUseCase = Depends(
        create_upsert_plex_server_admin_token_use_case
    ),
):
    """
    Replace the admin token in the database after validating it against Plex.

    Creates the DB row if missing (same as POST). Prefer POST for first-time setup.
    """
    return await _upsert_admin_token(request, use_case)
