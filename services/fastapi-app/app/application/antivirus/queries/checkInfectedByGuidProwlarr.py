"""Queries for antivirus scan operations."""
from typing import Optional, List
from app.domain.ports.repositories.antivirus.antivirusRepo import AntivirusRepoPort
from app.domain.models.antivirusScan import AntivirusScan


class CheckInfectedByGuidProwlarrQuery:
    """Query to check if a Prowlarr GUID has any infected files."""
    
    def __init__(self, repo: AntivirusRepoPort):
        self.repo = repo
    
    async def execute(self, guid_prowlarr: str) -> bool:
        """
        Check if there are any infected files for a given Prowlarr GUID.
        
        Args:
            guid_prowlarr: The Prowlarr GUID to check
            
        Returns:
            True if there are infected files, False otherwise
        """
        return await self.repo.has_infected_by_guid_prowlarr(guid_prowlarr)


class GetAntivirusScanByIdQuery:
    """Query to get an antivirus scan by its ID."""
    
    def __init__(self, repo: AntivirusRepoPort):
        self.repo = repo
    
    async def execute(self, antivirus_id: int) -> Optional[AntivirusScan]:
        """
        Get an antivirus scan by its ID.
        
        Args:
            antivirus_id: The ID of the antivirus scan
            
        Returns:
            AntivirusScan if found, None otherwise
        """
        return await self.repo.get_by_id(antivirus_id)


class GetAntivirusScansByGuidProwlarrQuery:
    """Query to get all antivirus scans by Prowlarr GUID."""
    
    def __init__(self, repo: AntivirusRepoPort):
        self.repo = repo
    
    async def execute(self, guid_prowlarr: str) -> List[AntivirusScan]:
        """
        Get all antivirus scans for a given Prowlarr GUID.
        
        Args:
            guid_prowlarr: The Prowlarr GUID to search for
            
        Returns:
            List of AntivirusScan items
        """
        return await self.repo.get_by_guid_prowlarr(guid_prowlarr)


class GetAntivirusScanByFilePathQuery:
    """Query to get an antivirus scan by file path."""
    
    def __init__(self, repo: AntivirusRepoPort):
        self.repo = repo
    
    async def execute(self, file_path: str) -> Optional[AntivirusScan]:
        """
        Get an antivirus scan by file path.
        
        Args:
            file_path: The file path to search for
            
        Returns:
            AntivirusScan if found, None otherwise
        """
        return await self.repo.get_by_file_path(file_path)


class GetInfectedItemsQuery:
    """Query to get all infected items."""
    
    def __init__(self, repo: AntivirusRepoPort):
        self.repo = repo
    
    async def execute(self) -> List[AntivirusScan]:
        """
        Get all infected items.
        
        Returns:
            List of infected AntivirusScan items
        """
        return await self.repo.get_infected_items()


class GetCleanItemsQuery:
    """Query to get all clean (non-infected) items."""
    
    def __init__(self, repo: AntivirusRepoPort):
        self.repo = repo
    
    async def execute(self) -> List[AntivirusScan]:
        """
        Get all clean (non-infected) items.
        
        Returns:
            List of clean AntivirusScan items
        """
        return await self.repo.get_clean_items()


class GetAllAntivirusScansQuery:
    """Query to get all antivirus scans."""
    
    def __init__(self, repo: AntivirusRepoPort):
        self.repo = repo
    
    async def execute(self) -> List[AntivirusScan]:
        """
        Get all antivirus scans.
        
        Returns:
            List of all AntivirusScan items
        """
        return await self.repo.get_all()

