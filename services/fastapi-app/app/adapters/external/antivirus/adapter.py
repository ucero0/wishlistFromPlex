"""Adapter for Antivirus infrastructure - bridges domain and infrastructure."""
import logging
import os

from app.domain.errors.antivirus import AntivirusError, AntivirusPathNotFoundError
from app.domain.models.external_connection import ExternalConnectionStatus
from app.domain.models.scanResult import ScanResult
from app.domain.ports.external.antivirus.antivirusProvider import AntivirusProvider
from app.infrastructure.externalApis.antivirus.client import AntivirusClient

logger = logging.getLogger(__name__)


class AntivirusAdapter(AntivirusProvider):
    """Adapter that converts between Antivirus infrastructure and domain models."""

    def __init__(self, client: AntivirusClient):
        self.client = client

    def scan(self, path: str) -> ScanResult:
        if not os.path.exists(path):
            raise AntivirusPathNotFoundError(f"Path does not exist: {path}")

        external_response = self.client.scan(path)
        return ScanResult(
            is_infected=external_response.is_infected,
            virus_name=external_response.virus_name,
            yara_matches=external_response.yara_matches,
            scanned_files=external_response.scanned_files,
            infected_files=external_response.infected_files,
        )

    def test_connection(self) -> ExternalConnectionStatus:
        try:
            connected = self.client.test_connection()
            if connected:
                return ExternalConnectionStatus(service="antivirus", connected=True)
            return ExternalConnectionStatus(
                service="antivirus",
                connected=False,
                error=f"Cannot connect to antivirus at {self.client._target()}",
            )
        except AntivirusError as exc:
            return ExternalConnectionStatus(
                service="antivirus", connected=False, error=exc.message
            )
        except Exception as exc:
            logger.exception("Unexpected error testing antivirus connection")
            return ExternalConnectionStatus(
                service="antivirus", connected=False, error=str(exc)
            )
