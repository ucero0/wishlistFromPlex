"""Tests for refresh-before-serve when Plex sync fails."""

from datetime import datetime, timezone

from unittest.mock import AsyncMock, patch



import pytest



from app.application.plex.use_cases.refresh_plex_library_paths_before_serve_use_case import (

    RefreshPlexLibraryPathsBeforeServeUseCase,

)

from app.domain.models.plex_library_path import PlexLibraryPath





class _FakePathRepo:

    def __init__(self, rows):

        self._rows = rows



    async def list_all(self, active_only: bool = True):

        return self._rows



    async def apply_disk_stats(self, rows):

        return None





@pytest.mark.asyncio

async def test_plex_sync_failure_still_attempts_refresh_and_records_error():

    sync = AsyncMock()

    sync.execute = AsyncMock(side_effect=ConnectionError("plex down"))

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

        sync,

        filesystem,

    )



    with patch(

        "app.application.plex.use_cases.refresh_plex_library_paths_before_serve_use_case.refresh_disk_stats_in_database",

        new_callable=AsyncMock,

        return_value=synced_at,

    ):

        meta = await use_case.execute()



    assert meta.plex_sync_attempted is True

    assert meta.plex_sync_ok is False

    assert meta.plex_sync_error == "plex down"

    assert meta.disk_stats_synced_at == synced_at

