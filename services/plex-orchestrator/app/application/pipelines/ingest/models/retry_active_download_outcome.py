"""Outcome of an immediate re-search/re-send after a failed torrent."""
from enum import Enum


class RetryActiveDownloadOutcome(str, Enum):
    SUCCESS = "success"
    NO_TORRENT = "no_torrent"
    SEND_FAILED = "send_failed"
    DEFERRED = "deferred"
