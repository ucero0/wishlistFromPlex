"""Use case for creating an antivirus scan."""
from app.domain.ports.repositories.antivirus.antivirusRepo import AntivirusRepoPort
from app.domain.models.antivirusScan import AntivirusScan


class CreateAntivirusScanUseCase:
    """Use case for creating a new antivirus scan."""
    
    def __init__(self, repo: AntivirusRepoPort):
        self.repo = repo
    
    async def execute(self, antivirus_scan: AntivirusScan) -> AntivirusScan:
        """
        Create a new antivirus scan.
        
        Args:
            antivirus_scan: The antivirus scan to create
            
        Returns:
            The created AntivirusScan with ID and timestamps
        """
        return await self.repo.create(antivirus_scan)

