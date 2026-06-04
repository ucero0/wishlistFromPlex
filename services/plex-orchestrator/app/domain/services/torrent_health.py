"""
Detect unhealthy Deluge torrents (downloading, incomplete).

Rules (first match wins):
- error: Deluge error state
- unfinishable: availability < 1 (or empty swarm) after unfinishable_active_minutes
- stalled: no payload bytes for stall_days, or partial with no 100% peer ever seen
"""
import time
from dataclasses import dataclass
from typing import Literal

from app.domain.models.torrent import Torrent
from app.domain.models.torrent_health_config import TorrentHealthConfig

UnhealthyReason = Literal["error", "unfinishable", "stalled"]

SECONDS_PER_HOUR = 3600
SECONDS_PER_DAY = 86400
SECONDS_PER_MINUTE = 60
ZERO_PROGRESS_CUTOFF = 1.0  # percent


@dataclass(frozen=True)
class TorrentHealthThresholds:
    """Timers for unhealthy detection (normal vs strict when VPN is healthy)."""

    grace_hours: int = 6
    min_availability: float = 1.0
    unfinishable_active_minutes: int = 20
    no_complete_copy_days: int = 2
    stall_days: int = 5

    @classmethod
    def from_config(
        cls, config: TorrentHealthConfig, *, strict: bool = False
    ) -> "TorrentHealthThresholds":
        if strict:
            return cls(
                grace_hours=config.strict_grace_hours,
                min_availability=config.min_availability,
                unfinishable_active_minutes=config.strict_unfinishable_active_minutes,
                no_complete_copy_days=config.strict_no_complete_copy_days,
                stall_days=config.strict_stall_days,
            )
        return cls(
            grace_hours=config.grace_hours,
            min_availability=config.min_availability,
            unfinishable_active_minutes=config.unfinishable_active_minutes,
            no_complete_copy_days=config.no_complete_copy_days,
            stall_days=config.stall_days,
        )


def _is_error_state(torrent: Torrent) -> bool:
    return (torrent.state or "").lower() == "error"


def _seconds_since_added(torrent: Torrent, *, now: float | None = None) -> float | None:
    if torrent.time_added is None:
        return None
    return (now if now is not None else time.time()) - torrent.time_added


def _is_incomplete(torrent: Torrent) -> bool:
    if torrent.is_finished or _is_error_state(torrent):
        return False
    return float(torrent.progress or 0) < 99.9


def _is_downloading(torrent: Torrent) -> bool:
    return (torrent.state or "").lower() == "downloading"


def _is_transferring(torrent: Torrent) -> bool:
    return (torrent.download_speed or 0) > 0


def _effective_active_seconds(torrent: Torrent, *, now: float | None = None) -> float | None:
    """Deluge active_time when present, otherwise time since the torrent was added."""
    active_time = torrent.active_time
    if active_time is not None:
        seconds = float(active_time)
        if seconds >= 0:
            return seconds
    return _seconds_since_added(torrent, now=now)


def _has_no_connections(torrent: Torrent) -> bool:
    return (torrent.num_seeds or 0) == 0 and (torrent.num_peers or 0) == 0


def _swarm_cannot_finish(torrent: Torrent, *, min_availability: float) -> bool:
    """True when libtorrent reports insufficient copies or the swarm is empty."""
    if torrent.availability is not None:
        return float(torrent.availability) < min_availability
    return _has_no_connections(torrent)


def _never_seen_complete(torrent: Torrent) -> bool:
    value = torrent.last_seen_complete
    if value is None:
        return False
    return int(value) == 0


def _seconds_without_download(torrent: Torrent) -> float | None:
    tsd = torrent.time_since_download
    if tsd is not None and float(tsd) >= 0:
        return float(tsd)
    if _is_transferring(torrent):
        return 0.0
    return _effective_active_seconds(torrent)


def _is_unfinishable(
    torrent: Torrent,
    *,
    min_availability: float,
    active_seconds: float,
    unfinishable_active_minutes: int,
) -> bool:
    if not _is_downloading(torrent):
        return False
    if active_seconds <= unfinishable_active_minutes * SECONDS_PER_MINUTE:
        return False
    return _swarm_cannot_finish(torrent, min_availability=min_availability)


def _is_stalled(
    torrent: Torrent,
    *,
    thresholds: TorrentHealthThresholds,
    since_added_seconds: float,
) -> bool:
    """
    Stuck despite a finishable-looking swarm: idle bytes, or partial with no 100% peer ever.
    Low availability / empty swarms are handled by unfinishable first.
    """
    if not _is_downloading(torrent):
        return False

    idle_seconds = _seconds_without_download(torrent)
    if idle_seconds is not None and idle_seconds >= thresholds.stall_days * SECONDS_PER_DAY:
        return True

    if (
        _never_seen_complete(torrent)
        and float(torrent.progress or 0) >= ZERO_PROGRESS_CUTOFF
        and not _swarm_cannot_finish(torrent, min_availability=thresholds.min_availability)
        and since_added_seconds >= thresholds.no_complete_copy_days * SECONDS_PER_DAY
    ):
        return True

    return False


def unhealthy_reason(
    torrent: Torrent,
    *,
    thresholds: TorrentHealthThresholds | None = None,
    now: float | None = None,
) -> UnhealthyReason | None:
    t = thresholds or TorrentHealthThresholds()

    if _is_error_state(torrent):
        return "error"

    if not _is_incomplete(torrent) or not _is_downloading(torrent):
        return None

    since_added = _seconds_since_added(torrent, now=now)
    if since_added is None or since_added < t.grace_hours * SECONDS_PER_HOUR:
        return None

    if _is_transferring(torrent):
        return None

    active_seconds = _effective_active_seconds(torrent, now=now)
    if active_seconds is None:
        return None

    if _is_unfinishable(
        torrent,
        min_availability=t.min_availability,
        active_seconds=active_seconds,
        unfinishable_active_minutes=t.unfinishable_active_minutes,
    ):
        return "unfinishable"

    if _is_stalled(torrent, thresholds=t, since_added_seconds=since_added):
        return "stalled"

    return None


def is_torrent_unhealthy(
    torrent: Torrent,
    *,
    thresholds: TorrentHealthThresholds | None = None,
    now: float | None = None,
) -> bool:
    return unhealthy_reason(torrent, thresholds=thresholds, now=now) is not None
