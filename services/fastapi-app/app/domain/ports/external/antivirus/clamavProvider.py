"""Port for ClamAV provider."""
from typing import Protocol
from app.domain.models.scanResult import ScanResult


class ClamAVProvider(Protocol):
    """Protocol for ClamAV provider - handles both ClamAV and YARA scanning."""
    
    def scan(self, path: str) -> ScanResult:
        """
        Scan a file or directory with ClamAV and YARA rules.
        The service automatically detects if the path is a file or directory.
        
        Args:
            path: Path to the file or directory to scan
            
        Returns:
            ScanResult with scan results including infection status, virus names, and YARA matches
        """
        ...
    
    def test_connection(self) -> bool:
        """Test connection to ClamAV daemon."""
        ...

