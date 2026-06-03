"""Tests for libtorrent-aligned torrent health detection."""
import time

from app.domain.models.torrent import Torrent
from app.domain.services.torrent_health import (
    TorrentHealthThresholds,
    is_torrent_unhealthy,
    unhealthy_reason,
)

FIVE_DAYS_SECONDS = 5 * 86400
ONE_DAY_SECONDS = 86400
NOW = 1_700_000_000.0
THRESHOLDS = TorrentHealthThresholds(
    grace_hours=6,
    min_availability=1.0,
    unfinishable_days=1,
    no_complete_copy_days=2,
    no_complete_zero_hours=12,
    stall_days=5,
    stall_no_peers_hours=24,
)


def test_grace_period_blocks_removal():
    t = Torrent(
        hash="a" * 40,
        file_name="x.mkv",
        state="Downloading",
        progress=0.0,
        last_seen_complete=0,
        availability=0.0,
        num_seeds=0,
        num_peers=0,
        time_added=NOW - 3600,
    )
    assert unhealthy_reason(t, thresholds=THRESHOLDS, now=NOW) is None


def test_no_complete_copy_at_zero_percent_with_peers():
    """0% + never saw complete — peers do not block removal."""
    t = Torrent(
        hash="a" * 40,
        file_name="x.mkv",
        state="Downloading",
        progress=0.0,
        last_seen_complete=0,
        availability=0.0,
        num_seeds=0,
        num_peers=1,
        time_added=NOW - (13 * 3600),
    )
    assert unhealthy_reason(t, thresholds=THRESHOLDS, now=NOW) == "no_complete_copy"


def test_unfinishable_when_availability_below_one():
    t = Torrent(
        hash="a" * 40,
        file_name="x.mkv",
        state="Downloading",
        progress=10.0,
        availability=0.5,
        last_seen_complete=NOW - 3600,
        num_seeds=1,
        num_peers=1,
        time_added=NOW - ONE_DAY_SECONDS - 60,
    )
    assert unhealthy_reason(t, thresholds=THRESHOLDS, now=NOW) == "unfinishable"


def test_no_complete_copy_for_partial_without_full_copy():
    t = Torrent(
        hash="a" * 40,
        file_name="x.mkv",
        state="Downloading",
        progress=5.0,
        last_seen_complete=0,
        availability=1.2,
        num_seeds=0,
        num_peers=2,
        time_added=NOW - (2 * ONE_DAY_SECONDS) - 60,
    )
    assert unhealthy_reason(t, thresholds=THRESHOLDS, now=NOW) == "no_complete_copy"


def test_stalled_after_day_without_connections():
    t = Torrent(
        hash="a" * 40,
        file_name="x.mkv",
        state="Downloading",
        progress=30.0,
        last_seen_complete=NOW - 3600,
        availability=1.5,
        num_seeds=0,
        num_peers=0,
        time_since_download=7200,
        time_added=NOW - (25 * 3600),
    )
    assert unhealthy_reason(t, thresholds=THRESHOLDS, now=NOW) == "stalled"


def test_stalled_after_days_without_download_even_with_peers():
    t = Torrent(
        hash="a" * 40,
        file_name="x.mkv",
        state="Downloading",
        progress=10.0,
        availability=1.5,
        time_since_download=FIVE_DAYS_SECONDS + 60,
        num_seeds=1,
        num_peers=2,
        last_seen_complete=NOW - 3600,
        time_added=NOW - FIVE_DAYS_SECONDS - 120,
    )
    assert unhealthy_reason(t, thresholds=THRESHOLDS, now=NOW) == "stalled"


def test_stalled_when_active_long_without_peers():
    t = Torrent(
        hash="a" * 40,
        file_name="x.mkv",
        state="Downloading",
        progress=45.0,
        time_since_download=-1,
        active_time=FIVE_DAYS_SECONDS + 60,
        num_seeds=0,
        num_peers=0,
        time_added=NOW - FIVE_DAYS_SECONDS - 120,
    )
    assert unhealthy_reason(t, thresholds=THRESHOLDS, now=NOW) == "stalled"


def test_unfinishable_beats_no_complete_when_both_apply():
    t = Torrent(
        hash="a" * 40,
        file_name="x.mkv",
        state="Downloading",
        progress=50.0,
        availability=0.2,
        last_seen_complete=0,
        time_added=NOW - (2 * ONE_DAY_SECONDS) - 60,
    )
    assert unhealthy_reason(t, thresholds=THRESHOLDS, now=NOW) == "unfinishable"


def test_not_unhealthy_while_downloading():
    t = Torrent(
        hash="a" * 40,
        file_name="x.mkv",
        state="Downloading",
        progress=10.0,
        availability=0.5,
        download_speed=1024,
        time_since_download=-1,
        time_added=NOW - FIVE_DAYS_SECONDS,
    )
    assert unhealthy_reason(t, thresholds=THRESHOLDS, now=NOW) is None


def test_error_state():
    t = Torrent(hash="a" * 40, file_name="x.mkv", state="error")
    assert is_torrent_unhealthy(t, thresholds=THRESHOLDS) is True


def test_not_unhealthy_during_grace():
    t = Torrent(
        hash="a" * 40,
        file_name="x.mkv",
        state="Downloading",
        progress=0.0,
        last_seen_complete=0,
        availability=0.0,
        time_added=time.time() - 300,
    )
    assert is_torrent_unhealthy(t, thresholds=THRESHOLDS) is False
