"""
Detect unhealthy Deluge torrents using libtorrent/Deluge semantics.

Signals (see libtorrent torrent_status and Deluge UI columns):
- availability (distributed_copies): < 1 means the swarm cannot supply a full copy.
- last_seen_complete: 0 means no peer has ever had 100% in this swarm.
- time_since_download / peers: stalled = no payload bytes; isolated = no connections.
"""
import time
from dataclasses import dataclass
from typing import Literal

from app.domain.models.torrent import Torrent
from app.domain.models.torrent_health_config import TorrentHealthConfig

UnhealthyReason = Literal[
    "error",
    "unfinishable",
    "no_complete_copy",
    "stalled",
]

SECONDS_PER_HOUR = 3600
SECONDS_PER_DAY = 86400
ZERO_PROGRESS_CUTOFF = 1.0  # percent


@dataclass(frozen=True)
class TorrentHealthThresholds:
    """Timers for unhealthy detection (normal vs strict when VPN is healthy)."""

    grace_hours: int = 6
    min_availability: float = 1.0
    unfinishable_days: int = 1
    no_complete_copy_days: int = 2
    no_complete_zero_hours: int = 12
    stall_days: int = 5
    stall_no_peers_hours: int = 24

    @classmethod
    def from_config(
        cls, config: TorrentHealthConfig, *, strict: bool = False
    ) -> "TorrentHealthThresholds":
        if strict:
            return cls(
                grace_hours=config.strict_grace_hours,
                min_availability=config.min_availability,
                unfinishable_days=config.strict_unfinishable_days,
                no_complete_copy_days=config.strict_no_complete_copy_days,
                no_complete_zero_hours=config.strict_no_complete_zero_hours,
                stall_days=config.strict_stall_days,
                stall_no_peers_hours=config.strict_stall_no_peers_hours,
            )
        return cls(
            grace_hours=config.grace_hours,
            min_availability=config.min_availability,
            unfinishable_days=config.unfinishable_days,
            no_complete_copy_days=config.no_complete_copy_days,
            no_complete_zero_hours=config.no_complete_zero_hours,
            stall_days=config.stall_days,
            stall_no_peers_hours=config.stall_no_peers_hours,
        )


def _is_error_state(torrent: Torrent) -> bool:
    return (torrent.state or "").lower() == "error"


def _active_seconds(torrent: Torrent, *, now: float | None = None) -> float | None:
    if torrent.time_added is None:
        return None
    return (now if now is not None else time.time()) - torrent.time_added


def _is_incomplete(torrent: Torrent) -> bool:
    if torrent.is_finished or _is_error_state(torrent):
        return False
    return float(torrent.progress or 0) < 99.9


def _is_transferring(torrent: Torrent) -> bool:
    return (torrent.download_speed or 0) > 0


def _never_seen_complete(torrent: Torrent) -> bool:
    value = torrent.last_seen_complete
    if value is None:
        return False
    return int(value) == 0


def _availability(torrent: Torrent) -> float | None:
    if torrent.availability is None:
        return None
    return float(torrent.availability)


def _is_unfinishable(torrent: Torrent, *, min_availability: float) -> bool:
    """Swarm cannot complete the torrent (libtorrent distributed_copies < 1)."""
    avail = _availability(torrent)
    return avail is not None and avail < min_availability


def _has_no_connections(torrent: Torrent) -> bool:
    return (torrent.num_seeds or 0) == 0 and (torrent.num_peers or 0) == 0


def _seconds_without_download(torrent: Torrent) -> float | None:
    """Seconds since last payload download; falls back to active_time when unknown."""
    tsd = torrent.time_since_download
    if tsd is not None and float(tsd) >= 0:
        return float(tsd)
    if _is_transferring(torrent):
        return 0.0
    active_time = torrent.active_time
    if active_time is not None and float(active_time) > 0:
        return float(active_time)
    return None


def _is_stalled(
    torrent: Torrent,
    *,
    stall_days: int,
    stall_no_peers_hours: int,
    active_seconds: float,
) -> bool:
    """
    No useful download progress: long idle time, or isolated with no peers/seeds.
    """
    if active_seconds >= stall_no_peers_hours * SECONDS_PER_HOUR and _has_no_connections(
        torrent
    ):
        return True

    idle_seconds = _seconds_without_download(torrent)
    if idle_seconds is not None and idle_seconds >= stall_days * SECONDS_PER_DAY:
        return True

    return False


def unhealthy_reason(
    torrent: Torrent,
    *,
    thresholds: TorrentHealthThresholds | None = None,
    now: float | None = None,
) -> UnhealthyReason | None:
    """
    First matching rule wins (libtorrent-aligned).

    unfinishable: availability < min (typically 1.0) — cannot finish with current swarm.
    no_complete_copy: last_seen_complete == 0 — never saw a full copy in the swarm.
    stalled: no payload bytes for stall_days, or no peers/seeds for stall_no_peers_hours.
    """
    t = thresholds or TorrentHealthThresholds()

    if _is_error_state(torrent):
        return "error"

    if not _is_incomplete(torrent):
        return None

    active_seconds = _active_seconds(torrent, now=now)
    if active_seconds is None:
        return None
    if active_seconds < t.grace_hours * SECONDS_PER_HOUR:
        return None

    if _is_transferring(torrent):
        return None

    if (
        _is_unfinishable(torrent, min_availability=t.min_availability)
        and active_seconds >= t.unfinishable_days * SECONDS_PER_DAY
    ):
        return "unfinishable"

    if _never_seen_complete(torrent):
        progress = float(torrent.progress or 0)
        zero_limit = t.no_complete_zero_hours * SECONDS_PER_HOUR
        copy_limit = t.no_complete_copy_days * SECONDS_PER_DAY
        if progress < ZERO_PROGRESS_CUTOFF and active_seconds >= zero_limit:
            return "no_complete_copy"
        if progress >= ZERO_PROGRESS_CUTOFF and active_seconds >= copy_limit:
            return "no_complete_copy"

    if _is_stalled(
        torrent,
        stall_days=t.stall_days,
        stall_no_peers_hours=t.stall_no_peers_hours,
        active_seconds=active_seconds,
    ):
        return "stalled"

    return None


def is_torrent_unhealthy(
    torrent: Torrent,
    *,
    thresholds: TorrentHealthThresholds | None = None,
    now: float | None = None,
) -> bool:
    return unhealthy_reason(torrent, thresholds=thresholds, now=now) is not None
