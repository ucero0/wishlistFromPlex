"""Port for Deluge provider."""
from typing import Protocol, Optional, List
from app.domain.models.torrent import Torrent

class DelugeProvider(Protocol):
    """Protocol for Deluge provider."""
    async def get_torrents(self) -> List[Torrent]:
        """Get torrents from Deluge."""
        ...
    
    async def get_torrent_status(self, hash: str) -> Torrent:
        """Get the status of a torrent from Deluge."""
        ...
    
    async def remove_torrent(self, hash: str, remove_data: bool = False) -> bool:
        """Remove a torrent from Deluge."""
        ...
    
    async def get_torrent_save_path(self, hash: str) -> Optional[str]:
        """Get the save path of a torrent from Deluge."""
        ...