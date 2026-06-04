"""Resolve which video paths to verify before ingest."""
from collections.abc import Callable


def collect_ingest_video_paths(
    scan_path: str,
    *,
    is_file: bool,
    path_exists: Callable[[str], bool],
    is_file_path: Callable[[str], bool],
    list_video_files: Callable[[str], list[str]],
) -> list[str]:
    """Return absolute paths of video files to integrity-check for a quarantine path."""
    if not path_exists(scan_path):
        return []
    if is_file:
        return [scan_path]
    if is_file_path(scan_path):
        return [scan_path]
    return list_video_files(scan_path)
