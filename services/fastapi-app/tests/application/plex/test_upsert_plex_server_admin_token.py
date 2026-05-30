"""Tests for UpsertPlexServerAdminTokenUseCase."""
import pytest

from app.application.plex.use_cases.upsert_plex_server_admin_token_use_case import (
    UpsertPlexServerAdminTokenUseCase,
)
from app.domain.models.plex_server_config import PlexServerConfig


class _FakeRepo:
    def __init__(self, existing: PlexServerConfig | None = None):
        self._existing = existing
        self.saved: str | None = None

    async def get_config(self):
        return self._existing

    async def upsert_admin_token(self, admin_token: str):
        self.saved = admin_token
        return PlexServerConfig(id=1, admin_token=admin_token)


class _FakeClient:
    def __init__(self):
        self.validated: list[str] = []

    async def validate_admin_token(self, admin_token: str) -> None:
        self.validated.append(admin_token)


@pytest.mark.asyncio
async def test_upsert_validates_and_creates():
    repo = _FakeRepo()
    client = _FakeClient()
    use_case = UpsertPlexServerAdminTokenUseCase(repo, client)

    config, masked, created = await use_case.execute("  my-token  ")

    assert created is True
    assert client.validated == ["my-token"]
    assert repo.saved == "my-token"
    assert masked == "my-t***"
    assert config.admin_token == "my-token"


@pytest.mark.asyncio
async def test_upsert_updates_existing():
    repo = _FakeRepo(PlexServerConfig(id=1, admin_token="old"))
    client = _FakeClient()
    use_case = UpsertPlexServerAdminTokenUseCase(repo, client)

    _, _, created = await use_case.execute("new-token")

    assert created is False
    assert repo.saved == "new-token"
