"""ClamAV client - infrastructure layer."""
import logging
import os
from typing import Optional
import pyclamd
import httpx
from app.core.config import settings
from app.domain.models.scanResult import ScanResult

logger = logging.getLogger(__name__)


class ClamAVClient:
    """Infrastructure client for ClamAV virus scanning with YARA rules support.
    
    YARA scanning is handled by the ClamAV container service, not in FastAPI.
    This client calls the scanning service in the ClamAV container.
    """
    
    def __init__(self):
        self.host = settings.clamav_host
        self.port = settings.clamav_port
        self.cd: Optional[pyclamd.ClamdNetworkSocket] = None
    
    def _connect(self) -> bool:
        """Connect to ClamAV daemon."""
        if self.cd is not None:
            try:
                # Test connection
                self.cd.ping()
                return True
            except:
                self.cd = None
        
        try:
            self.cd = pyclamd.ClamdNetworkSocket(self.host, self.port)
            self.cd.ping()
            logger.debug("Connected to ClamAV daemon")
            return True
        except Exception as e:
            logger.error(f"Error connecting to ClamAV: {e}")
            self.cd = None
            return False
    
    def _call_scan_service(self, path: str) -> dict:
        """
        Call the scanning HTTP service in ClamAV container.
        This service handles both ClamAV and YARA scanning.
        
        Args:
            path: Path to file or directory to scan (FastAPI container paths)
            
        Returns:
            Dictionary with scan results
        """
        try:
            # Map path to ClamAV container path
            # FastAPI paths: /downloads, /media
            # ClamAV paths: /scan/downloads, /scan/media
            clamav_path = path
            if path.startswith("/downloads"):
                clamav_path = path.replace("/downloads", "/scan/downloads", 1)
            elif path.startswith("/media"):
                clamav_path = path.replace("/media", "/scan/media", 1)
            
            # Call HTTP scanning service in antivirus container
            scan_service_url = f"http://{self.host}:3311/scan"
            
            with httpx.Client(timeout=600.0) as client:
                response = client.post(
                    scan_service_url,
                    json={"path": clamav_path},
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Scan service returned status {response.status_code}: {response.text}")
                    return {
                        "is_infected": False,
                        "virus_name": None,
                        "yara_matches": [],
                        "scanned_files": [],
                        "infected_files": [],
                        "error": f"Scan service error: {response.status_code}"
                    }
            
        except httpx.RequestError as e:
            logger.error(f"Error connecting to scan service: {e}")
            return {
                "is_infected": False,
                "virus_name": None,
                "yara_matches": [],
                "scanned_files": [],
                "infected_files": [],
                "error": f"Connection error: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Error calling scan service: {e}")
            return {
                "is_infected": False,
                "virus_name": None,
                "yara_matches": [],
                "scanned_files": [],
                "infected_files": [],
                "error": str(e)
            }
    
    def scan(self, path: str) -> ScanResult:
        """
        Scan a file or directory with ClamAV and YARA rules.
        Automatically detects if the path is a file or directory.
        
        YARA scanning is handled by the ClamAV container service.
        
        Args:
            path: Path to the file or directory to scan (FastAPI container paths)
            
        Returns:
            ScanResult with comprehensive scan results
        """
        if not os.path.exists(path):
            logger.error(f"Path does not exist: {path}")
            return ScanResult(
                is_infected=False,
                scanned_files=[],
                infected_files=[]
            )
        
        # Call the scanning service in ClamAV container
        # This service handles both ClamAV and YARA scanning
        result = self._call_scan_service(path)
        
        # Convert to ScanResult model
        return ScanResult(
            is_infected=result.get("is_infected", False),
            virus_name=result.get("virus_name"),
            yara_matches=result.get("yara_matches", []),
            scanned_files=result.get("scanned_files", []),
            infected_files=result.get("infected_files", [])
        )
    
    def test_connection(self) -> bool:
        """Test connection to ClamAV daemon."""
        return self._connect()

