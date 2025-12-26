"""Adapter for ClamAV infrastructure - bridges domain and infrastructure."""
from app.infrastructure.externalApis.clamav.client import ClamAVClient
from app.domain.ports.external.clamav.clamavProvider import ClamAVProvider
from app.domain.models.scanResult import ScanResult


class ClamAVAdapter(ClamAVProvider):
    """Adapter that converts between ClamAV infrastructure and domain models."""
    
    def __init__(self, client: ClamAVClient):
        self.client = client
    
    def scan(self, path: str) -> ScanResult:
        """Scan a file or directory with ClamAV and YARA rules."""
        return self.client.scan(path)
    
    def test_connection(self) -> bool:
        """Test connection to ClamAV daemon."""
        return self.client.test_connection()

