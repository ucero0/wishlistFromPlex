"""Tests for Deluge domain error types."""
import pytest

from app.domain.errors.deluge import (
    DelugeConnectionError,
    DelugeTorrentNotFoundError,
)


def test_deluge_connection_error_service_name():
    exc = DelugeConnectionError("daemon down")
    assert exc.service == "deluge"
    assert exc.message == "daemon down"


def test_deluge_torrent_not_found_includes_hash():
    exc = DelugeTorrentNotFoundError("abc123")
    assert exc.torrent_hash == "abc123"
    assert "abc123" in exc.message
