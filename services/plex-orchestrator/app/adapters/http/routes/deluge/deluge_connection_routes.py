"""Deluge connection health routes."""
from fastapi import APIRouter, Depends

from app.adapters.http.mappers.external_service_http_mapper import external_connection_to_json_response
from app.application.deluge.queries.test_deluge_connection_query import TestDelugeConnectionQuery
from app.factories.deluge.deluge_factory import create_test_deluge_connection_query

deluge_connection_routes = APIRouter(tags=["deluge"])


@deluge_connection_routes.get("/test-connection")
async def test_deluge_connection(
    deluge_query: TestDelugeConnectionQuery = Depends(create_test_deluge_connection_query),
):
    status = await deluge_query.execute()
    return external_connection_to_json_response(status)
