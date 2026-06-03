"""Tests for Deluge connection HTTP mapping."""
import json

from app.adapters.http.mappers.deluge_connection_http_mapper import (
    deluge_connection_to_json_response,
)
from app.domain.models.external_connection import ExternalConnectionStatus


def test_vpn_unhealthy_returns_503():
    response = deluge_connection_to_json_response(
        ExternalConnectionStatus(
            service="deluge",
            connected=True,
            vpn_required=True,
            vpn_healthy=False,
            error="Gluetun VPN unhealthy: timeout",
            error_type="connection",
        )
    )
    assert response.status_code == 503
    body = json.loads(response.body)
    assert body["vpn_healthy"] is False
    assert body["status"] == "unhealthy"


def test_vpn_healthy_with_stalled_swarm_still_returns_200():
    response = deluge_connection_to_json_response(
        ExternalConnectionStatus(
            service="deluge",
            connected=True,
            vpn_required=True,
            vpn_healthy=True,
            torrent_connectivity="stalled",
            total_download_bps=0,
        )
    )
    assert response.status_code == 200
    body = json.loads(response.body)
    assert body["status"] == "healthy"
    assert body["torrent_connectivity"] == "stalled"
