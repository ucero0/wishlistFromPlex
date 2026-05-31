"""Repository port for torrent downloads."""
from typing import Protocol, List, Optional
from app.domain.models.active_download import ActiveDownload


class ActiveDownloadRepositoryPort(Protocol):
    """Protocol for torrent download repository operations."""
    
    async def get_by_id(self, torrent_id: int) -> Optional[ActiveDownload]:
        """Get a torrent download by its ID."""
        ...
    
    async def get_by_uid(self, torrent_uid: str) -> Optional[ActiveDownload]:
        """Get a torrent download by its UID."""
        ...
    
    async def get_by_guid_plex(self, guid_plex: str) -> List[ActiveDownload]:
        """Get all torrent downloads for a Plex GUID."""
        ...
    
    async def is_guid_plex_downloading(self, guid_plex: str) -> bool:
        """Check if a Plex GUID has any active downloads."""
        ...
    
    async def get_by_guid_prowlarr(self, guid_prowlarr: str) -> Optional[ActiveDownload]:
        """Get a torrent download by its Prowlarr GUID."""
        ...

    async def has_by_media_identity(
        self,
        title: str,
        year: Optional[int],
        media_type: str,
    ) -> bool:
        """True if any torrent row matches normalized title/year/type (another Plex user)."""
        ...

    async def has_episode_queued(
        self,
        plex_guid: str,
        title: str,
        season: int,
        episode: int,
    ) -> bool:
        """True if this show episode is already tracked in active_downloads."""
        ...
    
    async def get_by_type(self, media_type: str) -> List[ActiveDownload]:
        """Get all torrent downloads by media type (movie or show)."""
        ...
    
    async def get_all(self) -> List[ActiveDownload]:
        """Get all torrent downloads."""
        ...
    
    async def create(self, torrent: ActiveDownload) -> ActiveDownload:
        """Create a new torrent download."""
        ...
    
    async def update(self, torrent: ActiveDownload) -> ActiveDownload:
        """Update an existing torrent download."""
        ...
    
    async def delete(self, torrent: ActiveDownload) -> None:
        """Delete a torrent download."""
        ...
    
    async def delete_by_id(self, torrent_id: int) -> bool:
        """Delete a torrent download by its ID. Returns True if deleted, False if not found."""
        ...

