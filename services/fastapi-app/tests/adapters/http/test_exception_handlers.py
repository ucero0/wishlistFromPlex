"""HTTP mapping for Plex auth and configuration errors."""
import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.adapters.http.exception_handlers import external_service_error_handler
from app.domain.errors.external import ExternalServiceError
from app.domain.errors.plex import (
    PlexServerAdminTokenNotConfiguredError,
    PlexServerAuthError,
    PlexUserAuthError,
)


@pytest.fixture
def app() -> FastAPI:
    application = FastAPI()
    application.add_exception_handler(
        ExternalServiceError, external_service_error_handler
    )

    @application.get("/server-auth")
    async def server_auth():
        raise PlexServerAuthError("invalid admin token")

    @application.get("/user-auth")
    async def user_auth():
        raise PlexUserAuthError("invalid user token")

    @application.get("/missing-admin")
    async def missing_admin():
        raise PlexServerAdminTokenNotConfiguredError("PLEX_SERVER_ADMIN_TOKEN missing")

    return application


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "path,status,error_type",
    [
        ("/server-auth", 401, "server_auth"),
        ("/user-auth", 401, "user_auth"),
        ("/missing-admin", 503, "configuration"),
    ],
)
async def test_plex_token_errors_map_to_expected_http_status(
    app: FastAPI, path: str, status: int, error_type: str
) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(path)

    assert response.status_code == status
    body = response.json()
    assert body["service"] == "plex"
    assert body["error_type"] == error_type
    assert body["detail"]
