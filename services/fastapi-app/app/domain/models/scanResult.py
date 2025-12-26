"""Domain model for antivirus scan results."""
from pydantic import BaseModel
from typing import Optional, List


class ScanResult(BaseModel):
    """Domain model for a scan result."""
    is_infected: bool
    virus_name: Optional[str] = None
    yara_matches: List[str] = []
    scanned_files: List[str] = []  # List of all files that were scanned
    infected_files: List[str] = []  # List of files that were infected

