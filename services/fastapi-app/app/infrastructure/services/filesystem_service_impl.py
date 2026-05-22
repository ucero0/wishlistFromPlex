"""Filesystem service implementation for infrastructure operations."""
import logging
import os
import shutil
from pathlib import Path

from app.domain.models.disk_usage import DiskUsageStats

logger = logging.getLogger(__name__)


class FilesystemServiceImpl:
    """Filesystem service implementation with injected base paths."""

    def __init__(self, quarantine_path: str):
        self.media_quarantine_path = Path(quarantine_path)

    def move_file(self, source_path: str, destination_path: str) -> bool:
        try:
            source = Path(source_path)
            destination = Path(destination_path)
            if not source.exists() or not source.is_file():
                return False
            if not destination.parent.exists():
                destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(destination))
            return True
        except Exception:
            return False

    def move_directory(self, source_path: str, destination_path: str) -> bool:
        try:
            source = Path(source_path)
            destination = Path(destination_path)
            if not source.exists() or not source.is_dir():
                return False
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(destination))
            return True
        except Exception:
            return False

    def get_quarantine_path(self) -> str:
        return str(self.media_quarantine_path)

    def build_path(self, *path_parts: str) -> str:
        return str(Path(*path_parts))

    def path_exists(self, path: str) -> bool:
        return Path(path).exists()

    def is_file(self, path: str) -> bool:
        return Path(path).is_file()

    def is_directory(self, path: str) -> bool:
        return Path(path).is_dir()

    def get_quarantine_file_path(self, filename: str) -> str:
        return str(self.media_quarantine_path / filename)

    def get_path_size_bytes(self, path: str) -> int:
        """Total size of a file or directory tree (bytes)."""
        target = Path(path)
        if not target.exists():
            raise ValueError(f"Path does not exist: {path}")
        if target.is_file():
            return target.stat().st_size
        total = 0
        for entry in target.rglob("*"):
            if entry.is_file():
                total += entry.stat().st_size
        return total

    def delete_file(self, file_path: str) -> bool:
        try:
            path = Path(file_path)
            if not path.exists() or not path.is_file():
                return False
            path.unlink()
            return True
        except Exception:
            return False

    def delete_directory(self, directory_path: str) -> bool:
        try:
            path = Path(directory_path)
            if not path.exists() or not path.is_dir():
                return False
            shutil.rmtree(path)
            return True
        except Exception:
            return False

    def move(self, source_path: str, destination_path: str) -> bool:
        try:
            source = Path(source_path)
            destination = Path(destination_path)
            if not source.exists():
                return False
            if not destination.parent.exists():
                destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(destination))
            return True
        except Exception:
            return False

    def explain_move_failure(self, source_path: str, destination_path: str) -> str:
        """Human-readable reason why ``move`` would fail (does not move files)."""
        source = Path(source_path)
        destination = Path(destination_path)
        if not source.exists():
            return f"Source does not exist: {source_path}"
        if destination.exists():
            return f"Destination already exists: {destination_path}"
        parent = destination.parent
        if not parent.exists():
            try:
                parent.mkdir(parents=True, exist_ok=True)
            except OSError as exc:
                return (
                    f"Cannot create destination parent {parent}: {exc}. "
                    "Check Plex library bind mounts and permissions on the fastapi container."
                )
        usage_root = parent if parent.exists() else source.parent
        try:
            free = shutil.disk_usage(str(usage_root)).free
            size = self.get_path_size_bytes(source_path)
            if free < size:
                return (
                    f"Not enough free space on {usage_root}: need {size} bytes, "
                    f"have {free} bytes free"
                )
        except (OSError, ValueError) as exc:
            return f"Cannot check disk space for {usage_root}: {exc}"
        if not os.access(str(parent), os.W_OK):
            return f"Destination parent not writable: {parent}"
        return (
            f"Move from {source_path} to {destination_path} failed "
            "(permissions, cross-device move, or filesystem error)"
        )

    def delete(self, path: str) -> bool:
        try:
            path_obj = Path(path)
            if not path_obj.exists():
                return False
            if path_obj.is_file():
                path_obj.unlink()
                return True
            if path_obj.is_dir():
                shutil.rmtree(path_obj)
                return True
            return False
        except Exception:
            return False

    def remove_non_media_files(self, path: str) -> int:
        video_extensions = {
            ".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".m4v",
            ".mpg", ".mpeg", ".3gp", ".ogv", ".ts", ".m2ts", ".mts", ".vob",
            ".divx", ".xvid", ".asf", ".rm", ".rmvb", ".f4v", ".mxf",
        }
        subtitle_extensions = {".srt", ".vtt", ".ass"}
        allowed_extensions = video_extensions | subtitle_extensions
        removed_count = 0

        try:
            path_obj = Path(path)
            if not path_obj.exists():
                return 0
            if path_obj.is_file():
                if path_obj.suffix.lower() not in allowed_extensions and self.delete_file(path):
                    return 1
                return 0
            if path_obj.is_dir():
                for file_path in path_obj.rglob("*"):
                    if file_path.is_file() and file_path.suffix.lower() not in allowed_extensions:
                        if self.delete_file(str(file_path)):
                            removed_count += 1
            return removed_count
        except Exception:
            return removed_count

    @staticmethod
    def _first_existing_path(path: str) -> Path:
        """Resolve to the nearest existing Path (file or directory) for volume/disk queries."""
        p = Path(path).expanduser()
        try:
            p = p.resolve(strict=False)
        except (OSError, RuntimeError):
            p = Path(path).expanduser()
        while not p.exists() and p != p.parent:
            p = p.parent
        if not p.exists():
            raise ValueError(f"No existing path on filesystem for {path!r}")
        return p

    def get_volume_root(self, path: str) -> str:
        p = self._first_existing_path(path)
        rp = p.resolve(strict=False)
        if os.name == "nt":
            vol, _rest = os.path.splitdrive(str(rp))
            if not vol:
                anchor = Path(rp).anchor
                return str(Path(anchor).resolve()) if anchor else str(rp)
            if vol.startswith("\\\\"):
                return vol if vol.endswith(os.sep) else vol + os.sep
            if vol.endswith(":"):
                return vol + os.sep
            return vol
        cur = rp if rp.is_dir() else rp.parent
        while True:
            try:
                if cur.is_mount():
                    return str(cur)
            except OSError:
                pass
            if cur == cur.parent:
                return str(cur)
            cur = cur.parent

    def get_disk_usage(self, path: str) -> DiskUsageStats:
        p = self._first_existing_path(path)
        if p.is_file():
            p = p.parent
        usage = shutil.disk_usage(str(p))
        return DiskUsageStats(
            total_bytes=int(usage.total),
            used_bytes=int(usage.used),
            free_bytes=int(usage.free),
        )

    def get_free_space_bytes(self, path: str) -> int:
        return self.get_disk_usage(path).free_bytes

