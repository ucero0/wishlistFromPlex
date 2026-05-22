"""Tests for DB-first free space in PlexLibraryDestinationSelector."""
from datetime import datetime, timedelta, timezone

import pytest

from app.domain.models.plexLibraryPath import PlexLibraryPath
from app.domain.services.plex_library_destination_selector import (
    PlexLibraryDestinationSelector,
)


class _FakeRepo:
    def __init__(self, paths: list[PlexLibraryPath]):
        self._paths = paths

    async def list_active_by_media_type(self, media_type):
        return [p for p in self._paths if p.media_type == media_type]


class _FakeFilesystem:
    def __init__(self):
        self.calls: list[str] = []

    def get_free_space_bytes(self, path: str) -> int:
        self.calls.append(path)
        return 999


@pytest.mark.asyncio
async def test_prefers_fresh_db_free_bytes_over_live_probe():
    now = datetime.now(timezone.utc)
    repo = _FakeRepo(
        [
            PlexLibraryPath(
                section_id="1",
                section_title="Movies",
                media_type="movie",
                path="/movies",
                free_bytes=50_000_000_000,
                disk_stats_synced_at=now,
            ),
        ]
    )
    fs = _FakeFilesystem()
    selector = PlexLibraryDestinationSelector(
        repo, fs, disk_stats_max_age_hours=6
    )

    chosen = await selector.select("movie", required_bytes=1_000_000)

    assert chosen.path == "/movies"
    assert fs.calls == []


@pytest.mark.asyncio
async def test_falls_back_to_live_probe_when_db_stats_stale():
    old = datetime.now(timezone.utc) - timedelta(hours=24)
    repo = _FakeRepo(
        [
            PlexLibraryPath(
                section_id="1",
                section_title="Movies",
                media_type="movie",
                path="/movies",
                free_bytes=100,
                disk_stats_synced_at=old,
            ),
        ]
    )
    fs = _FakeFilesystem()
    selector = PlexLibraryDestinationSelector(repo, fs, disk_stats_max_age_hours=6)

    chosen = await selector.select("movie", required_bytes=500)

    assert chosen.path == "/movies"
    assert fs.calls == ["/movies"]
