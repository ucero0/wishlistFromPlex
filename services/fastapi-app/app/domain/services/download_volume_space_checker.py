"""Check free space on the Deluge download / quarantine volume."""
import logging

from app.adapters.http.mappers.disk_size_format import format_bytes_for_display
from app.domain.services.filesystem_service import FilesystemService

logger = logging.getLogger(__name__)


class DownloadVolumeSpaceChecker:
    """Ensures the download path has enough free bytes before adding a torrent."""

    def __init__(
        self,
        filesystem: FilesystemService,
        download_path: str,
        *,
        min_free_buffer_bytes: int,
        default_required_bytes_when_unknown: int,
    ):
        self._filesystem = filesystem
        self._download_path = download_path
        self._buffer = min_free_buffer_bytes
        self._default_required = default_required_bytes_when_unknown

    def required_bytes_for_torrent(self, size_bytes: int | None) -> int:
        base = size_bytes if size_bytes and size_bytes > 0 else self._default_required
        return base + self._buffer

    def has_space_for_torrent(self, size_bytes: int | None) -> tuple[bool, int, int]:
        """
        Returns (ok, free_bytes, required_bytes).
        """
        required = self.required_bytes_for_torrent(size_bytes)
        try:
            free = self._filesystem.get_free_space_bytes(self._download_path)
        except (ValueError, OSError) as exc:
            logger.warning(
                "Cannot read free space for download path %r: %s",
                self._download_path,
                exc,
            )
            return False, 0, required
        return free >= required, free, required

    def defer_reason_for_torrent(self, size_bytes: int | None) -> str:
        ok, free, required = self.has_space_for_torrent(size_bytes)
        if ok:
            return ""
        return (
            f"Insufficient download volume space: need "
            f"{format_bytes_for_display(required)}, "
            f"free {format_bytes_for_display(free)} on {self._download_path}"
        )
