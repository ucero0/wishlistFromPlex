"""Tests for torrent health detection."""
from app.domain.models.torrent import Torrent
from app.domain.services.torrent_health import (
    is_low_availability,
    is_stale_transfer,
    is_torrent_error_state,
    is_torrent_unhealthy,
)

FIVE_DAYS_SECONDS = 5 * 86400


def test_is_torrent_error_state():
    t = Torrent(hash="a" * 40, file_name="x.mkv", state="Error")
    assert is_torrent_error_state(t) is True


def test_is_low_availability_when_below_threshold():
    t = Torrent(
        hash="a" * 40,
        file_name="x.mkv",
        state="Downloading",
        progress=10.0,
        availability=0.5,
    )
    assert is_low_availability(t, min_availability=1.0) is True


def test_is_not_low_availability_when_finished():
    t = Torrent(
        hash="a" * 40,
        file_name="x.mkv",
        state="Seeding",
        progress=100.0,
        availability=0.0,
    )
    assert is_low_availability(t, min_availability=1.0) is False


def test_is_stale_transfer_when_no_download_for_days():
    t = Torrent(
        hash="a" * 40,
        file_name="x.mkv",
        state="Downloading",
        progress=10.0,
        time_since_download=FIVE_DAYS_SECONDS + 60,
        time_since_upload=-1,
    )
    assert is_stale_transfer(t, no_transfer_days=5) is True


def test_is_not_stale_transfer_when_recent_activity():
    t = Torrent(
        hash="a" * 40,
        file_name="x.mkv",
        state="Downloading",
        progress=10.0,
        time_since_download=120,
    )
    assert is_stale_transfer(t, no_transfer_days=5) is False


def test_is_not_stale_transfer_when_only_upload_is_old():
    t = Torrent(
        hash="a" * 40,
        file_name="x.mkv",
        state="Downloading",
        progress=10.0,
        time_since_download=120,
        time_since_upload=FIVE_DAYS_SECONDS + 60,
    )
    assert is_stale_transfer(t, no_transfer_days=5) is False


def test_is_not_stale_transfer_when_download_active():
    t = Torrent(
        hash="a" * 40,
        file_name="x.mkv",
        state="Downloading",
        progress=10.0,
        time_since_download=-1,
        time_since_upload=FIVE_DAYS_SECONDS + 60,
    )
    assert is_stale_transfer(t, no_transfer_days=5) is False


def test_is_torrent_unhealthy_includes_error():
    t = Torrent(hash="a" * 40, file_name="x.mkv", state="error")
    assert is_torrent_unhealthy(t, min_availability=1.0, no_transfer_days=5) is True
