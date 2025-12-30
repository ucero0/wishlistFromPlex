"""Adapter for Antivirus infrastructure - bridges domain and infrastructure."""
import logging
import os
from app.infrastructure.externalApis.antivirus.client import AntivirusClient
from app.domain.ports.external.antivirus.antivirusProvider import AntivirusProvider
from app.domain.models.scanResult import ScanResult

logger = logging.getLogger(__name__)


class AntivirusAdapter(AntivirusProvider):
    """Adapter that converts between Antivirus infrastructure and domain models."""
    
    def __init__(self, client: AntivirusClient):
        self.client = client
    
    def scan(self, path: str) -> ScanResult:
        """
        Scan a file or directory with antivirus and YARA rules.
        Automatically detects if the path is a file or directory.
        
        Args:
            path: Path to the file or directory to scan (FastAPI container paths)
            
        Returns:
            ScanResult with comprehensive scan results
        """
        # Domain logic: validate path exists
        if not os.path.exists(path):
            logger.error(f"Path does not exist: {path}")
            return ScanResult(
                is_infected=False,
                scanned_files=[],
                infected_files=[]
            )
        
        # Call infrastructure client (external API)
        external_response = self.client.scan(path)
        
        # Convert from external schema to domain model
        return ScanResult(
            is_infected=external_response.is_infected,
            virus_name=external_response.virus_name,
            yara_matches=external_response.yara_matches,
            scanned_files=external_response.scanned_files,
            infected_files=external_response.infected_files
        )
    
    def test_connection(self) -> bool:
        """Test connection to antivirus daemon."""
        return self.client.test_connection()

