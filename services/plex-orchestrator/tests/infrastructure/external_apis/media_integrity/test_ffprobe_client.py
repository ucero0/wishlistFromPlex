"""Tests for ffprobe media integrity client."""
from unittest.mock import MagicMock, patch

from app.infrastructure.external_apis.media_integrity.ffprobe_client import (
    FfprobeMediaIntegrityClient,
)


def test_verify_file_rejects_missing_file(tmp_path):
    client = FfprobeMediaIntegrityClient()
    result = client.verify_file(str(tmp_path / "missing.mkv"))
    assert result.is_valid is False
    assert result.error == "not a file"


def test_verify_file_rejects_tiny_file(tmp_path):
    tiny = tmp_path / "tiny.mkv"
    tiny.write_bytes(b"x" * 10)
    client = FfprobeMediaIntegrityClient(min_file_bytes=1024)
    result = client.verify_file(str(tiny))
    assert result.is_valid is False
    assert "too small" in (result.error or "")


@patch("app.infrastructure.external_apis.media_integrity.ffprobe_client.subprocess.run")
def test_verify_file_accepts_valid_probe(mock_run, tmp_path):
    video = tmp_path / "movie.mkv"
    video.write_bytes(b"x" * 2048)
    mock_run.return_value = MagicMock(
        returncode=0,
        stdout="codec_name=h264\n",
        stderr="",
    )
    client = FfprobeMediaIntegrityClient(min_file_bytes=1024)
    result = client.verify_file(str(video))
    assert result.is_valid is True
    mock_run.assert_called_once()


@patch("app.infrastructure.external_apis.media_integrity.ffprobe_client.subprocess.run")
def test_verify_file_rejects_ffprobe_error(mock_run, tmp_path):
    video = tmp_path / "bad.mkv"
    video.write_bytes(b"x" * 2048)
    mock_run.return_value = MagicMock(
        returncode=1,
        stdout="",
        stderr="Invalid data found when processing input",
    )
    client = FfprobeMediaIntegrityClient(min_file_bytes=1024)
    result = client.verify_file(str(video))
    assert result.is_valid is False
    assert "Invalid data" in (result.error or "")
