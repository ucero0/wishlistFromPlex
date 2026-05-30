"""Filesystem service implementation for infrastructure operations."""
import logging
import os
import shutil
from pathlib import Path

from app.domain.models.disk_usage import DiskUsageStats

logger = logging.getLogger(__name__)


class FilesystemServiceImpl:
    """Filesystem service implementation with injected base paths."""

    def __init__(self, quarantine_path: str, host_fs_prefix: str = ""):
        self.media_quarantine_path = Path(quarantine_path)
        self._host_fs_prefix = host_fs_prefix.strip()

    def _to_plex_path(self, container_path: str) -> str:
        """Map a container-resolved path back to the Plex/host path (strip host prefix)."""
        prefix = self._host_fs_prefix.rstrip("/")
        norm = os.path.normpath(container_path)
        if not prefix:
            return norm
        if norm == prefix:
            return "/"
        prefix_with_sep = prefix + os.sep
        if norm.startswith(prefix_with_sep):
            rest = norm[len(prefix) :]
            return rest if rest else "/"
        return norm

    def _resolve_path(self, path: str) -> Path:
        """
        Resolve a Plex/host path to an existing path in this process.

        Tries the path as given first, then ``{host_fs_prefix}{absolute_path}`` when
        configured (Docker bind-mount of the host root at ``/host``, etc.).
        """
        direct = Path(path).expanduser()
        try:
            direct = direct.resolve(strict=False)
        except (OSError, RuntimeError):
            direct = Path(path).expanduser()
        if direct.exists():
            return direct

        prefix = self._host_fs_prefix.rstrip("/")
        if prefix and os.path.isabs(str(direct)):
            prefixed = Path(prefix + os.path.normpath(str(direct)))
            try:
                prefixed = prefixed.resolve(strict=False)
            except (OSError, RuntimeError):
                pass
            if prefixed.exists():
                return prefixed

        hint = (
            f"Set CONTAINER_HOST_FS_PREFIX (e.g. /host) and bind-mount the host filesystem "
            f"({prefix or 'HOST_FS_BIND_SOURCE'}:{prefix or '/host'}) in docker-compose."
            if not prefix
            else f"Ensure the host path exists under bind mount {prefix!r}."
        )
        raise ValueError(
            f"Path {path!r} does not exist on this host/container. {hint} "
            "See docs/DOCKER_SETUP.md."
        )

    def _resolve_move_destination(self, path: str) -> Path:
        """Resolve a move target; the final path may not exist yet (only its parent must)."""
        dest = Path(path).expanduser()
        if dest.exists():
            return self._resolve_path(path)
        parent = dest.parent
        if not parent or parent == dest:
            return self._resolve_path(path)
        resolved_parent = self._resolve_path(str(parent))
        return resolved_parent / dest.name

    def move_file(self, source_path: str, destination_path: str) -> bool:
        try:
            source = self._resolve_path(source_path)
            destination = self._resolve_move_destination(destination_path)
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
            source = self._resolve_path(source_path)
            destination = self._resolve_move_destination(destination_path)
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
        try:
            return self._resolve_path(path).exists()
        except ValueError:
            return False

    def is_file(self, path: str) -> bool:
        try:
            return self._resolve_path(path).is_file()
        except ValueError:
            return False

    def is_directory(self, path: str) -> bool:
        try:
            return self._resolve_path(path).is_dir()
        except ValueError:
            return False

    def get_quarantine_file_path(self, filename: str) -> str:
        return str(self.media_quarantine_path / filename)

    def get_path_size_bytes(self, path: str) -> int:
        """Total size of a file or directory tree (bytes)."""
        target = self._resolve_path(path)
        if target.is_file():
            return target.stat().st_size
        total = 0
        for entry in target.rglob("*"):
            if entry.is_file():
                total += entry.stat().st_size
        return total

    def delete_file(self, file_path: str) -> bool:
        try:
            path = self._resolve_path(file_path)
            if not path.exists() or not path.is_file():
                return False
            path.unlink()
            return True
        except Exception:
            return False

    def delete_directory(self, directory_path: str) -> bool:
        try:
            path = self._resolve_path(directory_path)
            if not path.exists() or not path.is_dir():
                return False
            shutil.rmtree(path)
            return True
        except Exception:
            return False

    def list_video_files(self, path: str) -> list[str]:
        video_extensions = {
            ".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".m4v",
            ".mpg", ".mpeg", ".3gp", ".ogv", ".ts", ".m2ts", ".mts", ".vob",
            ".divx", ".xvid", ".asf", ".rm", ".rmvb", ".f4v", ".mxf",
        }
        try:
            target = self._resolve_path(path)
            if not target.exists():
                return []
            if target.is_file():
                return [path] if target.suffix.lower() in video_extensions else []
            files: list[str] = []
            for entry in target.rglob("*"):
                if entry.is_file() and entry.suffix.lower() in video_extensions:
                    files.append(self._to_plex_path(str(entry)))
            return files
        except Exception:
            return []

    def move(self, source_path: str, destination_path: str) -> bool:
        try:
            source = self._resolve_path(source_path)
            destination = self._resolve_move_destination(destination_path)
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
        try:
            source = self._resolve_path(source_path)
            destination = self._resolve_move_destination(destination_path)
        except ValueError as exc:
            return str(exc)
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
                    "Check Plex library bind mounts and permissions on the plex-orchestrator container."
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
            path_obj = self._resolve_path(path)
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
            path_obj = self._resolve_path(path)
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
    def _decode_proc_mount_field(field: str) -> str:
        """Decode octal escape sequences in /proc/self/mounts fields (e.g. \\040 -> space)."""
        out: list[str] = []
        i = 0
        while i < len(field):
            if field[i] == "\\" and i + 3 < len(field):
                try:
                    out.append(chr(int(field[i + 1 : i + 4], 8)))
                    i += 4
                    continue
                except ValueError:
                    pass
            out.append(field[i])
            i += 1
        return "".join(out)

    @staticmethod
    def _read_mount_points() -> list[str]:
        mounts: list[str] = []
        try:
            with open("/proc/self/mounts", encoding="utf-8") as mounts_file:
                for line in mounts_file:
                    parts = line.split()
                    if len(parts) >= 2:
                        mounts.append(
                            FilesystemServiceImpl._decode_proc_mount_field(parts[1])
                        )
        except OSError:
            pass
        return mounts

    @staticmethod
    def _longest_mount_prefix(path: str, mount_points: list[str]) -> str:
        """Return the longest /proc/self/mounts target that contains ``path``."""
        norm = os.path.normpath(path)
        best = "/"
        best_len = 1
        for mount_point in mount_points:
            mp_norm = os.path.normpath(mount_point)
            if norm == mp_norm or norm.startswith(mp_norm + os.sep):
                if len(mp_norm) >= best_len:
                    best_len = len(mp_norm)
                    best = mp_norm
        return best

    def get_volume_root(self, path: str) -> str:
        p = self._resolve_path(path)
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

        usage_path = str(rp if rp.is_dir() else rp.parent)
        mount_points = self._read_mount_points()
        if mount_points:
            return self._to_plex_path(
                self._longest_mount_prefix(usage_path, mount_points)
            )

        cur = Path(usage_path)
        while True:
            try:
                if cur.is_mount():
                    return self._to_plex_path(str(cur))
            except OSError:
                pass
            if cur == cur.parent:
                return self._to_plex_path(str(cur))
            cur = cur.parent

    def get_disk_usage(self, path: str) -> DiskUsageStats:
        p = self._resolve_path(path)
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

