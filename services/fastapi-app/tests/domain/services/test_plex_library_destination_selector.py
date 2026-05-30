"""Tests for Plex library destination selection by free space."""
import pytest

from app.domain.errors.plex import (
    PlexLibraryPathNoSpaceError,
    PlexLibraryPathNotConfiguredError,
)
from app.domain.models.plex_library_path import PlexLibraryPath
from app.domain.plex.library_media_type import normalize_torrent_media_type
from app.domain.services.plex_library_destination_selector import (
    PlexLibraryDestinationSelector,
)


class _FakeRepo:
    def __init__(self, paths: list[PlexLibraryPath]):
        self._paths = paths

    async def list_active_by_media_type(self, media_type):
        return [p for p in self._paths if p.media_type == media_type]


class _FakeFilesystem:
    def __init__(self, free_by_path: dict[str, int]):
        self._free = free_by_path

    def get_free_space_bytes(self, path: str) -> int:
        if path not in self._free:
            raise ValueError("missing")
        return self._free[path]


@pytest.mark.parametrize(
    ("media", "expected"),
    [
        ("movie", "movie"),
        ("show", "tvshow"),
        ("tvshow", "tvshow"),
        ("episode", "other"),
    ],
)
def test_normalize_media_type(media, expected):
    assert normalize_torrent_media_type(media) == expected


@pytest.mark.asyncio
async def test_select_path_with_most_free_space():
    repo = _FakeRepo(
        [
            PlexLibraryPath(
                section_id="1",
                section_title="Movies",
                media_type="movie",
                path="/mnt/a",
            ),
            PlexLibraryPath(
                section_id="1",
                section_title="Movies",
                media_type="movie",
                path="/mnt/b",
            ),
        ]
    )
    fs = _FakeFilesystem({"/mnt/a": 1_000, "/mnt/b": 5_000_000})
    selector = PlexLibraryDestinationSelector(repo, fs)

    chosen = await selector.select("movie", required_bytes=2_000_000)

    assert chosen.path == "/mnt/b"


@pytest.mark.asyncio
async def test_select_raises_when_no_paths_in_db():
    selector = PlexLibraryDestinationSelector(_FakeRepo([]), _FakeFilesystem({}))
    with pytest.raises(PlexLibraryPathNotConfiguredError):
        await selector.select("movie", required_bytes=100)


@pytest.mark.asyncio
async def test_select_raises_when_no_space():
    repo = _FakeRepo(
        [
            PlexLibraryPath(
                section_id="1",
                section_title="Movies",
                media_type="movie",
                path="/mnt/full",
            ),
        ]
    )
    fs = _FakeFilesystem({"/mnt/full": 100})
    selector = PlexLibraryDestinationSelector(repo, fs)

    with pytest.raises(PlexLibraryPathNoSpaceError):
        await selector.select("movie", required_bytes=1_000_000)
