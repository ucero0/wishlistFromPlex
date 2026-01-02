from typing import Optional, List
from rapidfuzz import fuzz
import time
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
    """Query to get a torrent by its name using similarity matching and/or time_added."""
    def __init__(self, provider: DelugeProvider, similarity_threshold: float = 0.6):
        self.provider = provider
        self.similarity_threshold = similarity_threshold

    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """Calculate similarity ratio between two strings."""
        return fuzz.ratio(str1.lower(), str2.lower()) / 100.0

    async def execute(self, name: str, time_added_threshold: Optional[float] = None) -> Optional[Torrent]:
        """
        Execute the query to get a torrent by its name using similarity matching.
        If time_added_threshold is provided, prioritize torrents added within that time (in seconds) from now.
        
        Args:
            name: The name to search for
            time_added_threshold: Optional time threshold in seconds. If provided, torrents added
                                within this time from now will be prioritized over name similarity.
        """
        torrents: List[Torrent] = await self.provider.get_torrents()
        
        current_time = time.time()
        best_match = None
        best_similarity = 0.0
        
        # If time threshold is provided, first try to find torrents added within that time from now
        if time_added_threshold is not None:
            time_window_start = current_time - time_added_threshold
            for torrent in torrents:
                if torrent.time_added is not None:
                    # Check if torrent was added within the threshold from now (between time_window_start and current_time)
                    if time_window_start <= torrent.time_added <= current_time:
                        similarity = self._calculate_similarity(name, torrent.fileName)
                        if similarity > best_similarity:
                            best_similarity = similarity
                            best_match = torrent
            
            # If we found a match within the time threshold, return it (even with low similarity)
            # since time-based matching is more reliable for recently added torrents
            if best_match:
                return best_match
        
        # Fallback to name similarity matching if no time-based match found
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