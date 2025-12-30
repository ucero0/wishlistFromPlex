from typing import Optional, List
from rapidfuzz import fuzz
from app.domain.ports.external.deluge.delugeProvider import DelugeProvider
from app.domain.models.torrent import Torrent

class GetTorrentsStatusQuery:
    """Query to get the status of torrents."""
    def __init__(self, provider: DelugeProvider):
        self.provider = provider

    async def execute(self) -> List[Torrent]:
        """Execute the query to get the status of a torrent."""
        torrents:List[Torrent] = await self.provider.get_torrents()
        return torrents


class GetTorrentStatusQuery:
    """Query to get the status of a torrent."""
    def __init__(self, provider: DelugeProvider):
        self.provider = provider

    async def execute(self, hash: str) -> Torrent:
        """Execute the query to get the status of a torrent."""
        torrent:Torrent = await self.provider.get_torrent_status(hash)
        return torrent

class GetTorrentByNameQuery:
    """Query to get a torrent by its name using similarity matching."""
    def __init__(self, provider: DelugeProvider, similarity_threshold: float = 0.6):
        self.provider = provider
        self.similarity_threshold = similarity_threshold

    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """Calculate similarity ratio between two strings."""
        return fuzz.ratio(str1.lower(), str2.lower()) / 100.0

    async def execute(self, name: str) -> Optional[Torrent]:
        """Execute the query to get a torrent by its name using similarity matching."""
        torrents:List[Torrent] = await self.provider.get_torrents()
        
        best_match = None
        best_similarity = 0.0
        
        for torrent in torrents:
            similarity = self._calculate_similarity(name, torrent.fileName)
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = torrent
        
        # Return the best match if it meets the similarity threshold
        if best_match and best_similarity >= self.similarity_threshold:
            return best_match
        
        return None