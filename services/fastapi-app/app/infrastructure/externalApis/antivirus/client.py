"""Antivirus client - infrastructure layer."""
import logging
import httpx
from app.core.config import settings
from app.infrastructure.externalApis.antivirus.schemas import ExternalAntivirusScanResponse

logger = logging.getLogger(__name__)


class AntivirusClient:
    """Infrastructure client for antivirus virus scanning with YARA rules support.
    
    YARA scanning is handled by the antivirus container service, not in FastAPI.
    This client calls the scanning service in the antivirus container.
    """
    
    def __init__(self):
        self.host = settings.antivirus_host
        self.port = settings.antivirus_port
        self.scan_service_url = f"http://{self.host}:{self.port}/scan"
        self.health_url = f"http://{self.host}:{self.port}/health"
    
    def _connect(self) -> bool:
        """Test connection to antivirus HTTP scan service."""
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(self.health_url)
                if response.status_code == 200:
                    logger.debug("Connected to antivirus scan service")
                    return True
                return False
        except Exception as e:
            logger.error(f"Error connecting to antivirus scan service: {e}")
            return False
    
    def scan(self, path: str) -> ExternalAntivirusScanResponse:
        """
        Call the scanning HTTP service in antivirus container.
        This service handles both antivirus and YARA scanning.
        
        Args:
            path: Path to file or directory to scan (FastAPI container paths)
            
        Returns:
            ExternalAntivirusScanResponse with scan results from the external API
            
        Raises:
            httpx.HTTPStatusError: If the scan service returns a non-2xx status code
            httpx.RequestError: If there's a connection or timeout error
        """
        logger.info(f"Calling scan service at {self.scan_service_url} for path: {path}")
        
        with httpx.Client(timeout=600.0) as client:
            response = client.post(
                self.scan_service_url,
                json={"path": path},
                headers={"Content-Type": "application/json"},
                timeout=600.0
            )
            
            # Raise exception for non-2xx status codes
            response.raise_for_status()
            return ExternalAntivirusScanResponse(**response.json())
    
    def test_connection(self) -> bool:
        """Test connection to antivirus HTTP scan service."""
        return self._connect()

