"""Detect unhealthy Deluge torrents by availability and transfer activity."""
import time

from app.domain.models.torrent import Torrent

SECONDS_PER_DAY = 86400


def is_torrent_error_state(torrent: Torrent) -> bool:
    return (torrent.state or "").lower() == "error"


def torrent_active_seconds(torrent: Torrent, *, now: float | None = None) -> float | None:
    if torrent.time_added is None:
        return None
    return (now if now is not None else time.time()) - torrent.time_added


def is_low_availability(
    torrent: Torrent,
    *,
    min_availability: float,
    min_active_days: int = 1,
    now: float | None = None,
) -> bool:
    if torrent.is_finished or is_torrent_error_state(torrent):
        return False
    if torrent.availability is None:
        return False
    if float(torrent.availability) >= min_availability:
        return False
    active_seconds = torrent_active_seconds(torrent, now=now)
    if active_seconds is None:
        return False
    if active_seconds < min_active_days * SECONDS_PER_DAY:
        return False
    return True


def is_stale_transfer(
    torrent: Torrent,
    *,
    no_transfer_days: int,
) -> bool:
    """True when no download activity for longer than the threshold."""
    if torrent.is_finished or is_torrent_error_state(torrent):
        return False
    value = torrent.time_since_download
    if value is None or value < 0:
        return False
    threshold_seconds = no_transfer_days * SECONDS_PER_DAY
    return float(value) > threshold_seconds


def unhealthy_reason(
    torrent: Torrent,
    *,
    min_availability: float,
    no_transfer_days: int,
    min_availability_active_days: int = 1,
    now: float | None = None,
) -> str | None:
    if is_torrent_error_state(torrent):
        return "error"
    if is_low_availability(
        torrent,
        min_availability=min_availability,
        min_active_days=min_availability_active_days,
        now=now,
    ):
        return "low_availability"
    if is_stale_transfer(torrent, no_transfer_days=no_transfer_days):
        return "stale_transfer"
    return None


def is_torrent_unhealthy(
    torrent: Torrent,
    *,
    min_availability: float,
    no_transfer_days: int,
    min_availability_active_days: int = 1,
    now: float | None = None,
) -> bool:
    return unhealthy_reason(
        torrent,
        min_availability=min_availability,
        no_transfer_days=no_transfer_days,
        min_availability_active_days=min_availability_active_days,
        now=now,
    ) is not None
