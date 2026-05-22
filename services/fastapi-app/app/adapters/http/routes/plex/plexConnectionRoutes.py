"""Plex server connectivity health routes."""
from fastapi import APIRouter, Depends

from app.adapters.http.schemas.plex.plexConnectionSchemas import PlexConnectionResponse
from app.application.plex.queries.testPlexServerConnection import TestPlexServerConnectionQuery
from app.factories.plex.plexServerFactory import create_test_plex_server_connection_query

plex_connection_routes = APIRouter(tags=["plex"])


@plex_connection_routes.get("/test-connection", response_model=PlexConnectionResponse)
async def test_plex_server_connection(
    query: TestPlexServerConnectionQuery = Depends(create_test_plex_server_connection_query),
):
    status = await query.execute()
    return PlexConnectionResponse(
        connected=status.connected,
        status="healthy" if status.is_healthy else "unhealthy",
        service=status.service,
        error=status.error,
    )
