"""Tests for pre-ingest media integrity verification."""
from unittest.mock import MagicMock

from app.application.pipelines.ingest.use_cases.verify_media_integrity_use_case import (
    VerifyMediaIntegrityUseCase,
)
from app.domain.models.media_integrity_result import MediaIntegrityResult


def test_verify_collects_video_files_from_directory():
    filesystem = MagicMock()
    filesystem.path_exists.return_value = True
    filesystem.is_file.return_value = False
    filesystem.list_video_files.return_value = ["/plex2/show/episode.mkv"]
    filesystem.resolve_access_path.return_value = "/host/plex2/show/episode.mkv"
    provider = MagicMock()
    provider.verify.return_value = MediaIntegrityResult(
        is_valid=True,
        checked_files=["/host/plex2/show/episode.mkv"],
    )

    result = VerifyMediaIntegrityUseCase(filesystem, provider).execute(
        "/plex2/show", is_file=False
    )

    assert result.is_valid is True
    filesystem.resolve_access_path.assert_called_once_with("/plex2/show/episode.mkv")
    provider.verify.assert_called_once_with(["/host/plex2/show/episode.mkv"])
    assert result.checked_files == ["/plex2/show/episode.mkv"]


def test_verify_maps_corrupt_paths_back_to_logical():
    filesystem = MagicMock()
    filesystem.path_exists.return_value = True
    filesystem.is_file.return_value = True
    filesystem.list_video_files.return_value = []
    filesystem.resolve_access_path.return_value = "/host/plex2/bad.mkv"
    provider = MagicMock()
    provider.verify.return_value = MediaIntegrityResult(
        is_valid=False,
        checked_files=["/host/plex2/bad.mkv"],
        corrupt_files=["/host/plex2/bad.mkv"],
        file_errors={"/host/plex2/bad.mkv": "truncated"},
    )

    result = VerifyMediaIntegrityUseCase(filesystem, provider).execute(
        "/plex2/bad.mkv", is_file=True
    )

    assert result.corrupt_files == ["/plex2/bad.mkv"]
    assert result.file_errors == {"/plex2/bad.mkv": "truncated"}


def test_verify_fails_when_no_video_files():
    filesystem = MagicMock()
    filesystem.path_exists.return_value = True
    filesystem.is_file.return_value = False
    filesystem.list_video_files.return_value = []
    provider = MagicMock()

    result = VerifyMediaIntegrityUseCase(filesystem, provider).execute(
        "/q/empty", is_file=False
    )

    assert result.is_valid is False
    provider.verify.assert_not_called()
