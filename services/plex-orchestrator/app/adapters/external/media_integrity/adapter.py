"""Adapter bridging ffprobe infrastructure and domain media integrity models."""
from app.domain.models.external_connection import ExternalConnectionStatus
from app.domain.models.media_integrity_result import MediaIntegrityResult
from app.domain.ports.external.media_integrity.media_integrity_provider import (
    MediaIntegrityProvider,
)
from app.domain.services.connection_probe import capture_sync_connection_probe
from app.infrastructure.external_apis.media_integrity.ffprobe_client import (
    FfprobeMediaIntegrityClient,
)


class MediaIntegrityAdapter(MediaIntegrityProvider):
    def __init__(self, client: FfprobeMediaIntegrityClient):
        self._client = client

    def verify(self, paths: list[str]) -> MediaIntegrityResult:
        if not paths:
            return MediaIntegrityResult(
                is_valid=False,
                checked_files=[],
                corrupt_files=[],
                file_errors={},
            )

        probe_results = self._client.verify_files(paths)
        checked = [item.path for item in probe_results]
        corrupt = [item.path for item in probe_results if not item.is_valid]
        errors = {
            item.path: item.error or "unknown error"
            for item in probe_results
            if not item.is_valid and item.error
        }
        return MediaIntegrityResult(
            is_valid=len(corrupt) == 0,
            checked_files=checked,
            corrupt_files=corrupt,
            file_errors=errors,
        )

    def test_connection(self) -> ExternalConnectionStatus:
        return capture_sync_connection_probe(
            "media_integrity",
            self._client.probe_connection,
        )
