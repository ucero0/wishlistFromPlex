"""Use case for updating an antivirus scan."""
from app.domain.ports.repositories.antivirus.antivirusRepo import AntivirusRepoPort
from app.domain.models.antivirusScan import AntivirusScan


class UpdateAntivirusScanUseCase:
    """Use case for updating an existing antivirus scan."""
    
    def __init__(self, repo: AntivirusRepoPort):
        self.repo = repo
    
    async def execute(self, antivirus_scan: AntivirusScan) -> AntivirusScan:
        """
        Update an existing antivirus scan.
        
        Args:
            antivirus_scan: The antivirus scan to update (must have an ID)
            
        Returns:
            The updated AntivirusScan
        """
        return await self.repo.update(antivirus_scan)

