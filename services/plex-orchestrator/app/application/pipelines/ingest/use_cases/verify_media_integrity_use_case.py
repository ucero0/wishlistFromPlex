"""Verify quarantine video files before copying to the Plex library."""
from app.domain.models.media_integrity_result import MediaIntegrityResult
from app.domain.ports.external.media_integrity.media_integrity_provider import (
    MediaIntegrityProvider,
)
from app.domain.services.filesystem_service import FilesystemService
from app.domain.services.ingest_media_paths import collect_ingest_video_paths


class VerifyMediaIntegrityUseCase:
    def __init__(
        self,
        filesystem_service: FilesystemService,
        media_integrity_provider: MediaIntegrityProvider,
    ):
        self._filesystem_service = filesystem_service
        self._media_integrity_provider = media_integrity_provider

    def execute(self, scan_path: str, *, is_file: bool) -> MediaIntegrityResult:
        paths = collect_ingest_video_paths(
            scan_path,
            is_file=is_file,
            path_exists=self._filesystem_service.path_exists,
            is_file_path=self._filesystem_service.is_file,
            list_video_files=self._filesystem_service.list_video_files,
        )
        if not paths:
            return MediaIntegrityResult(
                is_valid=False,
                checked_files=[],
                corrupt_files=[],
                file_errors={scan_path: "no video files found"},
            )
        access_paths = [
            self._filesystem_service.resolve_access_path(path) for path in paths
        ]
        probe_result = self._media_integrity_provider.verify(access_paths)
        return self._to_logical_paths(probe_result, access_paths, paths)

    @staticmethod
    def _to_logical_paths(
        result: MediaIntegrityResult,
        access_paths: list[str],
        logical_paths: list[str],
    ) -> MediaIntegrityResult:
        """Map ffprobe paths back to Plex/quarantine paths for logs and API responses."""
        access_to_logical = dict(zip(access_paths, logical_paths))
        return MediaIntegrityResult(
            is_valid=result.is_valid,
            checked_files=[
                access_to_logical.get(path, path) for path in result.checked_files
            ],
            corrupt_files=[
                access_to_logical.get(path, path) for path in result.corrupt_files
            ],
            file_errors={
                access_to_logical.get(path, path): error
                for path, error in result.file_errors.items()
            },
        )
