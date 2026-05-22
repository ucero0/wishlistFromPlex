"""Port for Antivirus provider."""
from typing import Protocol

from app.domain.models.external_connection import ExternalConnectionStatus
from app.domain.models.scanResult import ScanResult


class AntivirusProvider(Protocol):
    """Protocol for Antivirus provider - handles both antivirus and YARA scanning."""

    def scan(self, path: str) -> ScanResult:
        ...

    def test_connection(self) -> ExternalConnectionStatus:
        """Probe connectivity (non-throwing health check)."""
        ...
