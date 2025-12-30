"""External schemas for Antivirus HTTP scan service API."""
from pydantic import BaseModel
from typing import List, Optional


class ExternalAntivirusScanResponse(BaseModel):
    """Raw scan response structure from Antivirus HTTP scan service - external schema.
    
    This represents the response structure from the antivirus container's HTTP scan service.
    The service returns this structure for both file and directory scans.
    """
    is_infected: bool
    virus_name: Optional[str] = None
    yara_matches: List[str] = []
    scanned_files: List[str] = []
    infected_files: List[str] = []
    error: Optional[str] = None
    file_path: Optional[str] = None  # Only present for single file scans
    
    class Config:
        """Pydantic configuration."""
        extra = "ignore"  # Ignore extra fields from external API

