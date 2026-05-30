"""Deluge connection health routes."""
import asyncio

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.adapters.http.mappers.external_service_http_mapper import (
    connection_status_to_http_status,
    connection_status_to_response_body,
)
from app.adapters.http.schemas.deluge.deluge_schemas import DelugeConnectionResponse
from app.adapters.http.schemas.gluetun.gluetun_schemas import VpnHealthSummary
from app.application.deluge.queries.test_deluge_connection_query import TestDelugeConnectionQuery
from app.application.gluetun.queries.test_gluetun_connection_query import TestGluetunConnectionQuery
from app.factories.deluge.deluge_factory import create_test_deluge_connection_query
from app.factories.gluetun.gluetun_factory import create_test_gluetun_connection_query

deluge_connection_routes = APIRouter(tags=["deluge"])


def _vpn_summary(status) -> VpnHealthSummary:
    return VpnHealthSummary(
        connected=status.connected,
        status="healthy" if status.is_healthy else "unhealthy",
        error=status.error,
    )


@deluge_connection_routes.get("/test-connection", response_model=DelugeConnectionResponse)
async def test_deluge_connection(
    deluge_query: TestDelugeConnectionQuery = Depends(create_test_deluge_connection_query),
    gluetun_query: TestGluetunConnectionQuery = Depends(create_test_gluetun_connection_query),
):
    deluge_status, vpn_status = await asyncio.gather(
        deluge_query.execute(),
        gluetun_query.execute(),
    )
    content = connection_status_to_response_body(
        deluge_status,
        vpn=_vpn_summary(vpn_status).model_dump(),
    )
    return JSONResponse(
        status_code=connection_status_to_http_status(deluge_status),
        content=content,
    )
