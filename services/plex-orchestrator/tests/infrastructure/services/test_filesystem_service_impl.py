"""Tests for Linux mount-point resolution and disk path validation."""
from __future__ import annotations

import pytest

from app.infrastructure.services.filesystem_service_impl import FilesystemServiceImpl


@pytest.fixture
def filesystem() -> FilesystemServiceImpl:
    return FilesystemServiceImpl("/tmp/quarantine")


def test_longest_mount_prefix_picks_deepest_mount(filesystem: FilesystemServiceImpl):
    mounts = ["/", "/mnt", "/mnt/media", "/plex2"]
    assert (
        filesystem._longest_mount_prefix("/mnt/media/movies", mounts) == "/mnt/media"
    )
    assert filesystem._longest_mount_prefix("/plex2/tvshows", mounts) == "/plex2"


def test_decode_proc_mount_field(filesystem: FilesystemServiceImpl):
    assert filesystem._decode_proc_mount_field("/mnt/my\\040media") == "/mnt/my media"


def test_missing_path_does_not_fall_back_to_root(filesystem: FilesystemServiceImpl):
    with pytest.raises(ValueError, match="does not exist"):
        filesystem.get_volume_root("/this/path/should/not/exist/anywhere")


def test_existing_path_resolves_to_mount_not_root(
    filesystem: FilesystemServiceImpl, tmp_path
):
    library = tmp_path / "movies"
    library.mkdir()
    root = filesystem.get_volume_root(str(library))
    assert root != ""


def test_disk_usage_requires_existing_path(filesystem: FilesystemServiceImpl):
    with pytest.raises(ValueError, match="does not exist"):
        filesystem.get_disk_usage("/nonexistent/plex/library/path")


def test_resolve_via_host_prefix(tmp_path):
    host_root = tmp_path / "host"
    library = host_root / "mnt" / "media" / "movies"
    library.mkdir(parents=True)
    fs = FilesystemServiceImpl("/tmp/quarantine", host_fs_prefix=str(host_root))
    resolved = fs._resolve_path("/mnt/media/movies")
    assert resolved == library
    usage = fs.get_disk_usage("/mnt/media/movies")
    assert usage.total_bytes > 0


def test_to_plex_path_strips_host_prefix():
    fs = FilesystemServiceImpl("/tmp/quarantine", host_fs_prefix="/host")
    assert fs._to_plex_path("/host/mnt/media") == "/mnt/media"
    assert fs._to_plex_path("/host") == "/"
    assert fs._to_plex_path("/other/path") == "/other/path"


def test_resolve_move_destination_allows_nonexistent_target(tmp_path):
    host_root = tmp_path / "host"
    library = host_root / "plex2" / "movies"
    library.mkdir(parents=True)
    fs = FilesystemServiceImpl("/tmp/quarantine", host_fs_prefix=str(host_root))
    resolved = fs._resolve_move_destination("/plex2/movies/New Movie (2026)")
    assert resolved == library / "New Movie (2026)"
    assert not resolved.exists()
