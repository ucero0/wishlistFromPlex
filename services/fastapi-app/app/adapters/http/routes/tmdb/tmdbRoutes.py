"""TMDB connectivity routes."""
from fastapi import APIRouter, Depends

from app.adapters.http.schemas.tmdb.tmdbSchemas import TmdbConnectionResponse
from app.application.tmdb.queries.testTmdbConnection import TestTmdbConnectionQuery
from app.factories.tmdb.tmdbFactory import create_test_tmdb_connection_query

tmdbRoutes = APIRouter(prefix="/tmdb", tags=["tmdb"])


@tmdbRoutes.get("/test-connection", response_model=TmdbConnectionResponse)
async def test_tmdb_connection(
    query: TestTmdbConnectionQuery = Depends(create_test_tmdb_connection_query),
):
    status = await query.execute()
    return TmdbConnectionResponse(
        connected=status.connected,
        status="healthy" if status.is_healthy else "unhealthy",
        service=status.service,
        error=status.error,
    )
