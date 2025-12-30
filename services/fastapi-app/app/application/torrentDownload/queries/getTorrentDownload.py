"""Queries for torrent download operations."""
from typing import Optional, List
from app.domain.ports.repositories.torrentDownload.torrentDownloadRepo import TorrentDownloadRepoPort
from app.domain.models.torrentDownload import TorrentDownload


class GetTorrentDownloadByIdQuery:
    """Query to get a torrent download by its ID."""
    
    def __init__(self, repo: TorrentDownloadRepoPort):
        self.repo = repo
    
    async def execute(self, torrent_id: int) -> Optional[TorrentDownload]:
        """
        Get a torrent download by its ID.
        
        Args:
            torrent_id: The ID of the torrent download
            
        Returns:
            TorrentDownload if found, None otherwise
        """
        return await self.repo.get_by_id(torrent_id)


class GetTorrentDownloadByUidQuery:
    """Query to get a torrent download by its UID."""
    
    def __init__(self, repo: TorrentDownloadRepoPort):
        self.repo = repo
    
    async def execute(self, torrent_uid: str) -> Optional[TorrentDownload]:
        """
        Get a torrent download by its UID.
        
        Args:
            torrent_uid: The UID of the torrent download
            
        Returns:
            TorrentDownload if found, None otherwise
        """
        return await self.repo.get_by_uid(torrent_uid)


class GetTorrentDownloadsByGuidPlexQuery:
    """Query to get all torrent downloads by Plex GUID."""
    
    def __init__(self, repo: TorrentDownloadRepoPort):
        self.repo = repo
    
    async def execute(self, guid_plex: str) -> List[TorrentDownload]:
        """
        Get all torrent downloads for a given Plex GUID.
        
        Args:
            guid_plex: The Plex GUID to search for
            
        Returns:
            List of TorrentDownload items
        """
        return await self.repo.get_by_guid_plex(guid_plex)


class IsGuidPlexDownloadingQuery:
    """Query to check if a Plex GUID has any active downloads."""
    
    def __init__(self, repo: TorrentDownloadRepoPort):
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


class GetTorrentDownloadByGuidProwlarrQuery:
    """Query to get a torrent download by Prowlarr GUID."""
    
    def __init__(self, repo: TorrentDownloadRepoPort):
        self.repo = repo
    
    async def execute(self, guid_prowlarr: str) -> Optional[TorrentDownload]:
        """
        Get a torrent download by its Prowlarr GUID.
        
        Args:
            guid_prowlarr: The Prowlarr GUID to search for
            
        Returns:
            TorrentDownload if found, None otherwise
        """
        return await self.repo.get_by_guid_prowlarr(guid_prowlarr)


class GetTorrentDownloadsByTypeQuery:
    """Query to get all torrent downloads by media type."""
    
    def __init__(self, repo: TorrentDownloadRepoPort):
        self.repo = repo
    
    async def execute(self, media_type: str) -> List[TorrentDownload]:
        """
        Get all torrent downloads by media type (movie or show).
        
        Args:
            media_type: The media type to filter by ("movie" or "show")
            
        Returns:
            List of TorrentDownload items
        """
        return await self.repo.get_by_type(media_type)


class GetAllTorrentDownloadsQuery:
    """Query to get all torrent downloads."""
    
    def __init__(self, repo: TorrentDownloadRepoPort):
        self.repo = repo
    
    async def execute(self) -> List[TorrentDownload]:
        """
        Get all torrent downloads.
        
        Returns:
            List of all TorrentDownload items
        """
        return await self.repo.get_all()

