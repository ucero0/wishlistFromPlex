"""Repository port for torrent downloads."""
from typing import Protocol, List, Optional
from app.domain.models.torrentDownload import TorrentDownload


class TorrentDownloadRepoPort(Protocol):
    """Protocol for torrent download repository operations."""
    
    async def get_by_id(self, torrent_id: int) -> Optional[TorrentDownload]:
        """Get a torrent download by its ID."""
        ...
    
    async def get_by_uid(self, torrent_uid: str) -> Optional[TorrentDownload]:
        """Get a torrent download by its UID."""
        ...
    
    async def get_by_guid_plex(self, guid_plex: str) -> List[TorrentDownload]:
        """Get all torrent downloads for a Plex GUID."""
        ...
    
    async def is_guid_plex_downloading(self, guid_plex: str) -> bool:
        """Check if a Plex GUID has any active downloads."""
        ...
    
    async def get_by_guid_prowlarr(self, guid_prowlarr: str) -> Optional[TorrentDownload]:
        """Get a torrent download by its Prowlarr GUID."""
        ...
    
    async def get_by_type(self, media_type: str) -> List[TorrentDownload]:
        """Get all torrent downloads by media type (movie or show)."""
        ...
    
    async def get_all(self) -> List[TorrentDownload]:
        """Get all torrent downloads."""
        ...
    
    async def create(self, torrent: TorrentDownload) -> TorrentDownload:
        """Create a new torrent download."""
        ...
    
    async def update(self, torrent: TorrentDownload) -> TorrentDownload:
        """Update an existing torrent download."""
        ...
    
    async def delete(self, torrent: TorrentDownload) -> None:
        """Delete a torrent download."""
        ...
    
    async def delete_by_id(self, torrent_id: int) -> bool:
        """Delete a torrent download by its ID. Returns True if deleted, False if not found."""
        ...

