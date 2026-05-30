"""TMDB connectivity routes."""
from fastapi import APIRouter, Depends

from app.adapters.http.mappers.external_service_http_mapper import (
    external_connection_to_json_response,
)
from app.adapters.http.schemas.tmdb.tmdb_schemas import TmdbConnectionResponse
from app.application.tmdb.queries.test_tmdb_connection_query import TestTmdbConnectionQuery
from app.factories.tmdb.tmdb_factory import create_test_tmdb_connection_query

tmdbRoutes = APIRouter(prefix="/tmdb", tags=["tmdb"])


@tmdbRoutes.get("/test-connection", response_model=TmdbConnectionResponse)
async def test_tmdb_connection(
    query: TestTmdbConnectionQuery = Depends(create_test_tmdb_connection_query),
):
    status = await query.execute()
    return external_connection_to_json_response(status)
