"""Adapter for Antivirus infrastructure - bridges domain and infrastructure."""
import logging
import os

from app.domain.errors.antivirus import AntivirusPathNotFoundError
from app.domain.models.external_connection import ExternalConnectionStatus
from app.domain.models.scan_result import ScanResult
from app.domain.ports.external.antivirus.antivirus_provider import AntivirusProvider
from app.domain.services.connection_probe import capture_sync_connection_probe
from app.infrastructure.external_apis.antivirus.client import AntivirusClient

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
        return capture_sync_connection_probe(
            "antivirus",
            self.client.probe_connection,
        )
