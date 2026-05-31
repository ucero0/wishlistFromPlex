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


def test_resolve_move_destination_allows_nested_new_show_folders(tmp_path):
    host_root = tmp_path / "host"
    library = host_root / "plex2" / "tvshows"
    library.mkdir(parents=True)
    fs = FilesystemServiceImpl("/tmp/quarantine", host_fs_prefix=str(host_root))
    resolved = fs._resolve_move_destination(
        "/plex2/tvshows/Scrubs (2001)/Season 01/Scrubs - s01e05 - My ABC's.mkv"
    )
    assert resolved == (
        library / "Scrubs (2001)" / "Season 01" / "Scrubs - s01e05 - My ABC's.mkv"
    )
    assert not resolved.exists()


def test_copy_file_leaves_source_intact(tmp_path):
    quarantine = tmp_path / "quarantine"
    library = tmp_path / "library"
    quarantine.mkdir()
    library.mkdir()
    source = quarantine / "movie.mkv"
    source.write_bytes(b"video-data")
    fs = FilesystemServiceImpl(str(quarantine))
    copied = fs.copy_file(str(source), str(library / "movie.mkv"))
    assert copied is True
    assert source.exists()
    assert (library / "movie.mkv").read_bytes() == b"video-data"


def test_copy_directory_leaves_source_intact(tmp_path):
    quarantine = tmp_path / "quarantine"
    library = tmp_path / "library"
    torrent_dir = quarantine / "Show S01"
    torrent_dir.mkdir(parents=True)
    (torrent_dir / "episode.mkv").write_bytes(b"ep")
    library.mkdir()
    fs = FilesystemServiceImpl(str(quarantine))
    copied = fs.copy_directory(str(torrent_dir), str(library / "Show S01"))
    assert copied is True
    assert torrent_dir.exists()
    assert (library / "Show S01" / "episode.mkv").exists()
