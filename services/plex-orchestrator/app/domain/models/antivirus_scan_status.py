"""Helpers for antivirus scan ingest state (no separate moved flag — use paths + Infected)."""
from pathlib import Path

from app.domain.models.antivirus_scan import AntivirusScan


def _path_under_quarantine(path: str, quarantine_root: str) -> bool:
    try:
        resolved = Path(path).resolve()
        root = Path(quarantine_root).resolve()
        return resolved == root or root in resolved.parents
    except (OSError, RuntimeError, ValueError):
        return path.startswith(quarantine_root.rstrip("/"))


def was_scanned_clean(scan: AntivirusScan) -> bool:
    """True if this DB row is a completed antivirus scan with no infection."""
    return not scan.is_infected


def is_clean_pending_ingest(scan: AntivirusScan, quarantine_root: str) -> bool:
    """
    Clean scan recorded and payload still in quarantine (move not done yet).

    After a successful move, file paths point at the library or folderPathDst is set.
    """
    if scan.is_infected:
        return False
    if scan.destination_folder_path:
        return False
    src = scan_path_from_record(scan)
    if not src:
        return False
    return _path_under_quarantine(src, quarantine_root)


def scan_path_from_record(scan: AntivirusScan) -> str | None:
    """Quarantine path for this scan (file or folder)."""
    return scan.file_path or scan.source_folder_path


def is_file_scan(scan: AntivirusScan) -> bool:
    return scan.file_path is not None
