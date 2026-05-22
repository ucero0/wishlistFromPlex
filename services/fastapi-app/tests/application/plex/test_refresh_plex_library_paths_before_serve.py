"""Tests for refresh-before-serve when Plex sync fails."""
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest

from app.application.plex.useCases.refreshPlexLibraryPathsBeforeServe import (
    RefreshPlexLibraryPathsBeforeServeUseCase,
)
from app.domain.models.plexLibraryPath import PlexLibraryPath


class _FakePathRepo:
    def __init__(self, rows):
        self._rows = rows

    async def list_all(self, active_only: bool = True):
        return self._rows

    async def apply_disk_stats(self, rows):
        return None


class _FakeUserRepo:
    async def get_active_users(self):
        return []


@pytest.mark.asyncio
async def test_plex_sync_failure_still_attempts_refresh_and_records_error():
    sync = AsyncMock(side_effect=ConnectionError("plex down"))
    filesystem = AsyncMock()
    path = PlexLibraryPath(
        section_id="1",
        section_title="Movies",
        media_type="movie",
        path="/mnt/movies",
    )
    synced_at = datetime.now(timezone.utc)
    use_case = RefreshPlexLibraryPathsBeforeServeUseCase(
        _FakePathRepo([path]),
        _FakeUserRepo(),
        sync,
        filesystem,
    )

    with patch(
        "app.application.plex.useCases.refreshPlexLibraryPathsBeforeServe.refresh_disk_stats_in_database",
        new_callable=AsyncMock,
        return_value=synced_at,
    ):
        meta = await use_case.execute(user_token="tok")

    assert meta.plex_sync_attempted is True
    assert meta.plex_sync_ok is False
    assert meta.plex_sync_error == "plex down"
    assert meta.disk_stats_synced_at == synced_at
