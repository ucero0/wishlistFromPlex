"""Repository port for antivirus scans."""
from typing import Protocol, List, Optional
from app.domain.models.antivirusScan import AntivirusScan


class AntivirusRepoPort(Protocol):
    """Protocol for antivirus scan repository operations."""
    
    async def get_by_id(self, antivirus_id: int) -> Optional[AntivirusScan]:
        """Get an antivirus scan by its ID."""
        ...
    
    async def get_by_guid_prowlarr(self, guid_prowlarr: str) -> List[AntivirusScan]:
        """Get all antivirus scans by Prowlarr GUID."""
        ...
    
    async def has_infected_by_guid_prowlarr(self, guid_prowlarr: str) -> bool:
        """Check if there are any infected files for a given Prowlarr GUID."""
        ...
    
    async def get_by_file_path(self, file_path: str) -> Optional[AntivirusScan]:
        """Get an antivirus scan by file path."""
        ...
    
    async def get_infected_items(self) -> List[AntivirusScan]:
        """Get all infected items."""
        ...
    
    async def get_clean_items(self) -> List[AntivirusScan]:
        """Get all clean (non-infected) items."""
        ...
    
    async def get_all(self) -> List[AntivirusScan]:
        """Get all antivirus scans."""
        ...
    
    async def create(self, antivirus_scan: AntivirusScan) -> AntivirusScan:
        """Create a new antivirus scan."""
        ...
    
    async def update(self, antivirus_scan: AntivirusScan) -> AntivirusScan:
        """Update an existing antivirus scan."""
        ...
    
    async def delete(self, antivirus_scan: AntivirusScan) -> None:
        """Delete an antivirus scan."""
        ...
    
    async def delete_by_id(self, antivirus_id: int) -> bool:
        """Delete an antivirus scan by its ID. Returns True if deleted, False if not found."""
        ...
    
    async def delete_by_guid_prowlarr(self, guid_prowlarr: str) -> int:
        """Delete all antivirus scans by Prowlarr GUID. Returns the number of deleted items."""
        ...

