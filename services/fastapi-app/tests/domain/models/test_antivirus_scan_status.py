"""Tests for antivirus ingest pending-move helpers."""
from datetime import datetime

from app.domain.models.antivirus_scan import AntivirusScan
from app.domain.models.antivirus_scan_status import (
    is_clean_pending_ingest,
    is_file_scan,
    scan_path_from_record,
    was_scanned_clean,
)

QUARANTINE = "/downloads/quarantine"


def _scan(**kwargs) -> AntivirusScan:
    defaults = {
        "prowlarr_guid": "guid-1",
        "is_infected": False,
        "scanned_at": datetime(2026, 1, 1),
    }
    defaults.update(kwargs)
    return AntivirusScan(**defaults)


def test_was_scanned_clean():
    assert was_scanned_clean(_scan()) is True
    assert was_scanned_clean(_scan(is_infected=True)) is False


def test_is_clean_pending_ingest_file_in_quarantine():
    s = _scan(file_path=f"{QUARANTINE}/movie.mkv")
    assert is_clean_pending_ingest(s, QUARANTINE) is True


def test_is_clean_pending_ingest_file_already_moved():
    s = _scan(file_path="/library/movies/movie.mkv")
    assert is_clean_pending_ingest(s, QUARANTINE) is False


def test_is_clean_pending_ingest_folder_pending():
    s = _scan(source_folder_path=f"{QUARANTINE}/show")
    assert is_clean_pending_ingest(s, QUARANTINE) is True


def test_is_clean_pending_ingest_folder_moved():
    s = _scan(
        source_folder_path=f"{QUARANTINE}/show",
        destination_folder_path="/library/tv/show",
    )
    assert is_clean_pending_ingest(s, QUARANTINE) is False


def test_scan_path_from_record_file():
    s = _scan(file_path="/q/movie.mkv")
    assert scan_path_from_record(s) == "/q/movie.mkv"
    assert is_file_scan(s) is True
