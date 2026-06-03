"""HTTP mapping for Deluge connection health (VPN + informational swarm stats)."""
from fastapi.responses import JSONResponse

from app.adapters.http.mappers.external_service_http_mapper import (
    connection_status_to_response_body,
    http_status_for_error_type,
)
from app.domain.models.external_connection import ExternalConnectionStatus


def deluge_connection_http_status(status: ExternalConnectionStatus) -> int:
    if not status.connected:
        return http_status_for_error_type(status.error_type or "connection")
    if status.vpn_required and status.vpn_healthy is False:
        return http_status_for_error_type("connection")
    return 200


def deluge_connection_to_json_response(status: ExternalConnectionStatus) -> JSONResponse:
    overall = "healthy"
    if not status.connected:
        overall = "unhealthy"
    elif status.vpn_required and status.vpn_healthy is False:
        overall = "unhealthy"

    content = connection_status_to_response_body(status)
    content["status"] = overall

    if status.vpn_required is not None:
        content["vpn_required"] = status.vpn_required
    if status.vpn_healthy is not None:
        content["vpn_healthy"] = status.vpn_healthy
    if status.vpn_required and status.vpn_healthy is False:
        content["error"] = status.error
        content["error_type"] = status.error_type or "connection"

    for field in (
        "torrent_connectivity",
        "dht_nodes",
        "has_incoming_connections",
        "downloading_count",
        "active_download_count",
        "total_download_bps",
        "total_peer_count",
    ):
        value = getattr(status, field, None)
        if value is not None:
            content[field] = value

    return JSONResponse(
        status_code=deluge_connection_http_status(status),
        content=content,
    )
