"""Tests for shared external-service HTTP status mapping."""
from app.adapters.http.mappers.external_service_http_mapper import (
    external_connection_to_json_response,
    http_status_for_error_type,
)
from app.domain.models.external_connection import ExternalConnectionStatus


def test_healthy_connection_returns_200():
    response = external_connection_to_json_response(
        ExternalConnectionStatus(service="plex", connected=True)
    )
    assert response.status_code == 200
    body = response.body.decode()
    assert '"connected":true' in body.replace(" ", "")
    assert '"status":"healthy"' in body.replace(" ", "")


def test_unreachable_server_returns_503_with_connection_error_type():
    response = external_connection_to_json_response(
        ExternalConnectionStatus(
            service="plex",
            connected=False,
            error="Cannot connect to Plex server at http://plex:32400",
            error_type="connection",
        )
    )
    assert response.status_code == 503
    body = response.body.decode()
    assert '"error_type":"connection"' in body.replace(" ", "")


def test_invalid_admin_token_returns_401():
    response = external_connection_to_json_response(
        ExternalConnectionStatus(
            service="plex",
            connected=False,
            error="Invalid Plex server admin token",
            error_type="server_auth",
        )
    )
    assert response.status_code == 401


def test_operation_error_returns_502():
    assert http_status_for_error_type("operation") == 502
    response = external_connection_to_json_response(
        ExternalConnectionStatus(
            service="plex",
            connected=False,
            error="library search failed for http://plex:32400: HTTP 500",
            error_type="operation",
        )
    )
    assert response.status_code == 502


def test_missing_configuration_returns_503():
    response = external_connection_to_json_response(
        ExternalConnectionStatus(
            service="tmdb",
            connected=False,
            error="TMDB API key is not configured",
            error_type="configuration",
        )
    )
    assert response.status_code == 503


def test_unhealthy_without_error_type_defaults_to_connection_503():
    response = external_connection_to_json_response(
        ExternalConnectionStatus(
            service="plex",
            connected=False,
            error="Something went wrong",
        )
    )
    assert response.status_code == 503
    body = response.body.decode()
    assert '"error_type":"connection"' in body.replace(" ", "")
