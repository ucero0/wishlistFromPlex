"""Result models for the watchlist download orchestration run."""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel


class WatchlistItemProcessOutcome(str, Enum):
    SENT_TO_DELUGE = "sent_to_deluge"
    DEFERRED = "deferred"
    NO_TORRENT = "no_torrent"
    SEND_FAILED = "send_failed"


class ProcessPlexWatchlistDownloadsResult(BaseModel):
    """Summary of one watchlist download orchestration run."""

    deferred_released: int = 0
    deferred_still_pending: int = 0
    deluge_reconcile_skipped: bool = False
    deluge_reconcile_reason: str | None = None
    deluge_removed: int = 0
    deluge_updated: int = 0
    deluge_total_checked: int = 0
    watchlist_entries: int = 0
    skipped_already_in_library: int = 0
    skipped_already_queued: int = 0
    sent_to_deluge: int = 0
    deferred: int = 0
    no_torrent: int = 0
    send_failed: int = 0

    @property
    def processed(self) -> int:
        return self.sent_to_deluge + self.deferred + self.no_torrent + self.send_failed

    @property
    def skipped(self) -> int:
        return self.skipped_already_in_library + self.skipped_already_queued


class SchedulerJobInfo(BaseModel):
    id: str
    name: str
    interval_minutes: int | None = None
    next_run_time: str | None = None


class RunSchedulerJobResponse(BaseModel):
    job_id: str
    job_name: str
    message: str
    watchlist_downloads: ProcessPlexWatchlistDownloadsResult | None = None
    deferred: dict | None = None
    library_paths: dict | None = None
    deluge_maintenance: dict | None = None
