"""Port for Deluge provider."""
from typing import Protocol
from app.domain.models.torrent import ListTorrents

class DelugeProvider(Protocol):
    """Protocol for Deluge provider."""
    async def get_torrents(self) -> ListTorrents:
        """Get torrents from Deluge."""
        ...
        