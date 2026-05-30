"""Plex server connectivity health routes."""
from fastapi import APIRouter, Depends

from app.adapters.http.mappers.external_service_http_mapper import (
    external_connection_to_json_response,
)
from app.adapters.http.schemas.plex.plex_connection_schemas import PlexConnectionResponse
from app.application.plex.queries.test_plex_server_connection_query import TestPlexServerConnectionQuery
from app.application.plex.queries.test_plex_server_admin_token_query import (
    TestPlexServerAdminTokenQuery,
)
from app.factories.plex.plex_server_factory import (
    create_test_plex_server_admin_token_query,
    create_test_plex_server_connection_query,
)

plex_connection_routes = APIRouter(tags=["plex"])


@plex_connection_routes.get(
    "/test-connection",
    response_model=PlexConnectionResponse,
    responses={
        502: {"description": "Plex API error", "model": PlexConnectionResponse},
        503: {"description": "Plex server unreachable", "model": PlexConnectionResponse},
    },
)
async def test_plex_server_connection(
    query: TestPlexServerConnectionQuery = Depends(create_test_plex_server_connection_query),
):
    """Probe Plex server reachability (no token required)."""
    status = await query.execute()
    return external_connection_to_json_response(status)


@plex_connection_routes.get(
    "/test-admin-token",
    response_model=PlexConnectionResponse,
    responses={
        401: {"description": "Invalid or unauthorized admin token", "model": PlexConnectionResponse},
        502: {"description": "Plex API error", "model": PlexConnectionResponse},
        503: {
            "description": "Missing token or unreachable server",
            "model": PlexConnectionResponse,
        },
    },
)
async def test_plex_server_admin_token(
    query: TestPlexServerAdminTokenQuery = Depends(create_test_plex_server_admin_token_query),
):
    """Validate PLEX_SERVER_ADMIN_TOKEN against library/sections on the local server."""
    status = await query.execute()
    return external_connection_to_json_response(status)
