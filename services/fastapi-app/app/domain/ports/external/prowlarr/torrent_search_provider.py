"""Port (Protocol) for torrent search provider."""
from typing import Protocol, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.infrastructure.externalApis.prowlarr.schemas import ProwlarrIndexer

from app.domain.models.torrent_search import TorrentSearchResult


class TorrentSearchProvider(Protocol):
    """Protocol defining the contract for torrent search operations."""
    
    async def search_torrents(
        self, 
        query: str, 
        media_type: str = "movie"
    ) -> List[TorrentSearchResult]:
        """
        Search for torrents and return domain models.
        
        Args:
            query: Search query string
            media_type: Type of media ('movie' or 'tv')
            
        Returns:
            List of TorrentSearchResult domain models
        """
        ...
    
    async def send_to_download_client(
        self, 
        guid: str, 
        indexer_id: int
    ) -> bool:
        """
        Send torrent to download client.
        
        Args:
            guid: Torrent GUID (magnet link or URL)
            indexer_id: Indexer ID
            
        Returns:
            True if successful, False otherwise
        """
        ...
    
    async def test_connection(self) -> tuple[bool, Optional[str], Optional[str]]:
        """
        Test connection to search provider.
        
        Returns:
            Tuple of (success: bool, version: Optional[str], error: Optional[str])
        """
        ...
    
    async def get_indexers(self) -> List["ProwlarrIndexer"]:
        """
        Get all indexers from the search provider (raw data, no filtering).
        
        Returns:
            List of all indexers from the provider
        """
        ...

