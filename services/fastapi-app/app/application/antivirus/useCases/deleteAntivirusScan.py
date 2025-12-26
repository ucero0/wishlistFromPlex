"""Use case for deleting an antivirus scan."""
from app.domain.ports.repositories.antivirus.antivirusRepo import AntivirusRepoPort
from app.domain.models.antivirusScan import AntivirusScan


class DeleteAntivirusScanUseCase:
    """Use case for deleting an antivirus scan."""
    
    def __init__(self, repo: AntivirusRepoPort):
        self.repo = repo
    
    async def execute(self, antivirus_scan: AntivirusScan) -> None:
        """
        Delete an antivirus scan.
        
        Args:
            antivirus_scan: The antivirus scan to delete (must have an ID)
        """
        await self.repo.delete(antivirus_scan)


class DeleteAntivirusScanByIdUseCase:
    """Use case for deleting an antivirus scan by ID."""
    
    def __init__(self, repo: AntivirusRepoPort):
        self.repo = repo
    
    async def execute(self, antivirus_id: int) -> bool:
        """
        Delete an antivirus scan by its ID.
        
        Args:
            antivirus_id: The ID of the antivirus scan to delete
            
        Returns:
            True if deleted, False if not found
        """
        return await self.repo.delete_by_id(antivirus_id)


class DeleteAntivirusScansByGuidProwlarrUseCase:
    """Use case for deleting all antivirus scans by Prowlarr GUID."""
    
    def __init__(self, repo: AntivirusRepoPort):
        self.repo = repo
    
    async def execute(self, guid_prowlarr: str) -> int:
        """
        Delete all antivirus scans for a given Prowlarr GUID.
        
        Args:
            guid_prowlarr: The Prowlarr GUID to delete scans for
            
        Returns:
            The number of deleted items
        """
        return await self.repo.delete_by_guid_prowlarr(guid_prowlarr)

