"""Port for rapid pre-ingest media integrity checks."""
from typing import Protocol

from app.domain.models.external_connection import ExternalConnectionStatus
from app.domain.models.media_integrity_result import MediaIntegrityResult


class MediaIntegrityProvider(Protocol):
    """Probe video files for container/readability issues before copying to the library."""

    def verify(self, paths: list[str]) -> MediaIntegrityResult:
        ...

    def test_connection(self) -> ExternalConnectionStatus:
        """Probe that the integrity backend (e.g. ffprobe) is available."""
        ...
