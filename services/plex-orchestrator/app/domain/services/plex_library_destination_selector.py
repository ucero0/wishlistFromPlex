"""Select a Plex library root path with enough free space for ingest."""
import logging
from datetime import datetime, timedelta, timezone

from app.domain.errors.plex import (
    PlexLibraryPathNoSpaceError,
    PlexLibraryPathNotConfiguredError,
)
from app.domain.models.plex_library_path import PlexLibraryPath
from app.domain.plex.library_media_type import normalize_torrent_media_type
from app.domain.ports.repositories.plex.plex_library_path_repository_port import PlexLibraryPathRepoPort
from app.domain.services.filesystem_service import FilesystemService

logger = logging.getLogger(__name__)


class PlexLibraryDestinationSelector:
    """
    Picks the active DB path with the most free space that fits the payload.

    Prefers ``free_bytes`` from ``plex_library_paths`` when stats are fresh;
    falls back to a live host probe when DB stats are missing or stale.
    """

    def __init__(
        self,
        path_repo: PlexLibraryPathRepoPort,
        filesystem: FilesystemService,
        *,
        disk_stats_max_age_hours: int = 6,
    ):
        self._path_repo = path_repo
        self._filesystem = filesystem
        self._disk_stats_max_age_hours = disk_stats_max_age_hours

    async def select(
        self, media_type: str, required_bytes: int
    ) -> PlexLibraryPath:
        kind = normalize_torrent_media_type(media_type)
        candidates = await self._path_repo.list_active_by_media_type(kind)
        if not candidates:
            raise PlexLibraryPathNotConfiguredError(
                f"No Plex library paths in database for media type '{kind}'. "
                "Call POST /plex/servers/library/locations-by-media/sync with a Plex user token first."
            )

        best: PlexLibraryPath | None = None
        best_free = -1
        errors: list[str] = []

        for candidate in candidates:
            free, source = self._effective_free_bytes(candidate)
            if free is None:
                errors.append(f"{candidate.path}: no disk stats")
                continue
            if free >= required_bytes and free > best_free:
                best = candidate
                best_free = free
                logger.debug(
                    "Candidate %s free=%s bytes (source=%s)",
                    candidate.path,
                    free,
                    source,
                )

        if best is None:
            paths_list = ", ".join(c.path for c in candidates)
            detail = "; ".join(errors) if errors else "all paths below required free space"
            raise PlexLibraryPathNoSpaceError(
                f"No Plex library path with >= {required_bytes} bytes free for '{kind}'. "
                f"Candidates: {paths_list}. ({detail})"
            )

        logger.info(
            "Selected Plex destination %s (section %s, free=%s bytes)",
            best.path,
            best.section_id,
            best_free,
        )
        return best

    def _effective_free_bytes(
        self, candidate: PlexLibraryPath
    ) -> tuple[int | None, str]:
        if self._db_free_bytes_fresh(candidate):
            return candidate.free_bytes, "db"

        try:
            return self._filesystem.get_free_space_bytes(candidate.path), "live"
        except (ValueError, OSError) as exc:
            logger.warning("Live disk probe failed for %s: %s", candidate.path, exc)
            if candidate.free_bytes is not None and candidate.disk_stats_error is None:
                return candidate.free_bytes, "db_stale"
            return None, "none"

    def _db_free_bytes_fresh(self, candidate: PlexLibraryPath) -> bool:
        if candidate.free_bytes is None or candidate.disk_stats_error:
            return False
        synced = candidate.disk_stats_synced_at
        if synced is None:
            return False
        if synced.tzinfo is None:
            synced = synced.replace(tzinfo=timezone.utc)
        max_age = timedelta(hours=self._disk_stats_max_age_hours)
        return datetime.now(timezone.utc) - synced <= max_age

