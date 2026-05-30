"""Tests for external-service error classification."""
import pytest

from app.domain.errors.plex import (
    PlexConnectionError,
    PlexOperationError,
    PlexServerAdminTokenNotConfiguredError,
    PlexServerAuthError,
)
from app.domain.errors.tmdb import TMDBConfigurationError, TMDBOperationError
from app.domain.services.external_error_classifier import classify_external_service_error


@pytest.mark.parametrize(
    "exc,expected",
    [
        (PlexServerAuthError("bad token"), "server_auth"),
        (PlexServerAdminTokenNotConfiguredError("missing"), "configuration"),
        (PlexConnectionError("down"), "connection"),
        (PlexOperationError("HTTP 500"), "operation"),
        (TMDBConfigurationError("missing key"), "configuration"),
        (TMDBOperationError("HTTP 500"), "operation"),
    ],
)
def test_classify_external_service_error(exc, expected: str) -> None:
    assert classify_external_service_error(exc) == expected
