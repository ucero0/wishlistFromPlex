"""Deluge connection health routes."""
import asyncio

from fastapi import APIRouter, Depends

from app.adapters.http.schemas.deluge.delugeSchemas import DelugeConnectionResponse
from app.adapters.http.schemas.gluetun.gluetunSchemas import VpnHealthSummary
from app.application.deluge.queries.testDelugeConnection import TestDelugeConnectionQuery
from app.application.gluetun.queries.testGluetunConnection import TestGluetunConnectionQuery
from app.factories.deluge.delugeFactory import create_test_deluge_connection_query
from app.factories.gluetun.gluetunFactory import create_test_gluetun_connection_query

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
    return DelugeConnectionResponse(
        connected=deluge_status.connected,
        status="healthy" if deluge_status.is_healthy else "unhealthy",
        service=deluge_status.service,
        error=deluge_status.error,
        vpn=_vpn_summary(vpn_status),
    )
