"""Antivirus client - infrastructure layer."""
import logging

import httpx

from app.core.config import settings
from app.domain.errors.antivirus import (
    AntivirusConnectionError,
    AntivirusOperationError,
)
from app.infrastructure.externalApis.antivirus.schemas import ExternalAntivirusScanResponse
from app.infrastructure.http_errors import raise_mapped_httpx_error

logger = logging.getLogger(__name__)


class AntivirusClient:
    """Infrastructure client for the antivirus HTTP scan service."""

    def __init__(self):
        self.host = settings.antivirus_host
        self.port = settings.antivirus_port
        self.scan_service_url = f"http://{self.host}:{self.port}/scan"
        self.health_url = f"http://{self.host}:{self.port}/health"

    def _target(self) -> str:
        return f"{self.host}:{self.port}"

    def _ensure_connected(self) -> None:
        if not self.test_connection():
            raise AntivirusConnectionError(
                f"Cannot connect to antivirus scan service at {self._target()}"
            )

    def test_connection(self) -> bool:
        """Probe antivirus HTTP health endpoint."""
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(self.health_url)
                return response.status_code == 200
        except Exception as exc:
            logger.error(
                "Error connecting to antivirus scan service at %s: %s",
                self._target(),
                exc,
            )
            return False

    def scan(self, path: str) -> ExternalAntivirusScanResponse:
        """Scan a file or directory via the antivirus HTTP service."""
        self._ensure_connected()
        logger.info("Calling scan service at %s for path: %s", self.scan_service_url, path)
        try:
            with httpx.Client(timeout=600.0) as client:
                response = client.post(
                    self.scan_service_url,
                    json={"path": path},
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()
                return ExternalAntivirusScanResponse(**response.json())
        except (AntivirusConnectionError, AntivirusOperationError):
            raise
        except Exception as exc:
            raise_mapped_httpx_error(
                exc,
                connection_error_type=AntivirusConnectionError,
                operation_error_type=AntivirusOperationError,
                target=self._target(),
                operation="antivirus scan",
            )
