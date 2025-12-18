"""Adapter for Prowlarr - bridges infrastructure and domain."""
import logging
from typing import List, Optional
from app.domain.ports.external.prowlarr.torrent_search_provider import TorrentSearchProvider
from app.infrastructure.externalApis.prowlarr.prowlarr_client import ProwlarrClient
from app.infrastructure.externalApis.prowlarr.schemas import ProwlarrIndexer
from app.domain.models.torrent_search import TorrentSearchResult
from app.adapters.external.prowlarr.mapper import to_domain_list

logger = logging.getLogger(__name__)


class ProwlarrAdapter(TorrentSearchProvider):
    """Adapter that converts Prowlarr infrastructure to domain models."""
    
    def __init__(self, client: ProwlarrClient):
        self.client = client
    
    async def search_torrents(
        self, 
        query: str, 
        media_type: str = "movie"
    ) -> List[TorrentSearchResult]:
        """Search for torrents and return domain TorrentSearchResult objects."""
        categories = "2000" if media_type == "movie" else "5000"
        logger.info(f"Searching Prowlarr: '{query}', media_type: {media_type}")
        
        # Client returns validated ProwlarrRawResult objects
        raw_results = await self.client.search(query, categories)
        
        # Convert infrastructure DTOs to domain models using mapper
        results = to_domain_list(raw_results)
        
        logger.info(f"Prowlarr returned {len(results)} validated results")
        return results
    
    async def send_to_download_client(self, guid: str, indexer_id: int) -> bool:
        """Send torrent to download client via Prowlarr."""
        return await self.client.send_to_download_client(guid, indexer_id)
    
    async def test_connection(self) -> tuple[bool, Optional[str], Optional[str]]:
        """Test connection to Prowlarr."""
        return await self.client.test_connection()
    
    async def get_indexers(self) -> List[ProwlarrIndexer]:
        """Get all indexers from Prowlarr (raw data, no filtering)."""
        return await self.client.get_indexers()

