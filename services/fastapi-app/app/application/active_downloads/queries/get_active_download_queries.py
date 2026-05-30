"""Queries for torrent download operations."""
from typing import Optional, List
from app.domain.ports.repositories.active_downloads.active_download_repository_port import ActiveDownloadRepositoryPort
from app.domain.models.active_download import ActiveDownload


class GetActiveDownloadByIdQuery:
    """Query to get a torrent download by its ID."""
    
    def __init__(self, repo: ActiveDownloadRepositoryPort):
        self.repo = repo
    
    async def execute(self, torrent_id: int) -> Optional[ActiveDownload]:
        """
        Get a torrent download by its ID.
        
        Args:
            torrent_id: The ID of the torrent download
            
        Returns:
            ActiveDownload if found, None otherwise
        """
        return await self.repo.get_by_id(torrent_id)


class GetActiveDownloadByUidQuery:
    """Query to get a torrent download by its UID."""
    
    def __init__(self, repo: ActiveDownloadRepositoryPort):
        self.repo = repo
    
    async def execute(self, torrent_uid: str) -> Optional[ActiveDownload]:
        """
        Get a torrent download by its UID.
        
        Args:
            torrent_uid: The UID of the torrent download
            
        Returns:
            ActiveDownload if found, None otherwise
        """
        return await self.repo.get_by_uid(torrent_uid)


class GetActiveDownloadsByGuidPlexQuery:
    """Query to get all torrent downloads by Plex GUID."""
    
    def __init__(self, repo: ActiveDownloadRepositoryPort):
        self.repo = repo
    
    async def execute(self, guid_plex: str) -> List[ActiveDownload]:
        """
        Get all torrent downloads for a given Plex GUID.
        
        Args:
            guid_plex: The Plex GUID to search for
            
        Returns:
            List of ActiveDownload items
        """
        return await self.repo.get_by_guid_plex(guid_plex)


class IsGuidPlexDownloadingQuery:
    """Query to check if a Plex GUID has any active downloads."""
    
    def __init__(self, repo: ActiveDownloadRepositoryPort):
        self.repo = repo
    
    async def execute(self, guid_plex: str) -> bool:
        """
        Check if a Plex GUID has any active downloads.
        
        Args:
            guid_plex: The Plex GUID to check
            
        Returns:
            True if there are any downloads for this GUID, False otherwise
        """
        return await self.repo.is_guid_plex_downloading(guid_plex)


class GetActiveDownloadByGuidProwlarrQuery:
    """Query to get a torrent download by Prowlarr GUID."""
    
    def __init__(self, repo: ActiveDownloadRepositoryPort):
        self.repo = repo
    
    async def execute(self, guid_prowlarr: str) -> Optional[ActiveDownload]:
        """
        Get a torrent download by its Prowlarr GUID.
        
        Args:
            guid_prowlarr: The Prowlarr GUID to search for
            
        Returns:
            ActiveDownload if found, None otherwise
        """
        return await self.repo.get_by_guid_prowlarr(guid_prowlarr)


class GetActiveDownloadsByTypeQuery:
    """Query to get all torrent downloads by media type."""
    
    def __init__(self, repo: ActiveDownloadRepositoryPort):
        self.repo = repo
    
    async def execute(self, media_type: str) -> List[ActiveDownload]:
        """
        Get all torrent downloads by media type (movie or show).
        
        Args:
            media_type: The media type to filter by ("movie" or "show")
            
        Returns:
            List of ActiveDownload items
        """
        return await self.repo.get_by_type(media_type)


class GetAllActiveDownloadsQuery:
    """Query to get all torrent downloads."""
    
    def __init__(self, repo: ActiveDownloadRepositoryPort):
        self.repo = repo
    
    async def execute(self) -> List[ActiveDownload]:
        """
        Get all torrent downloads.
        
        Returns:
            List of all ActiveDownload items
        """
        return await self.repo.get_all()

