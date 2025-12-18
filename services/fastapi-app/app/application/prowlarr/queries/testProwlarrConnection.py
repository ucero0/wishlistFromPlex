"""Query for testing Prowlarr connection."""
from typing import Optional
from app.domain.ports.external.prowlarr.torrent_search_provider import TorrentSearchProvider


class TestProwlarrConnectionQuery:
    """Query for testing connection to Prowlarr."""
    
    def __init__(self, search_provider: TorrentSearchProvider):
        self.search_provider = search_provider
    
    async def execute(self) -> tuple[bool, Optional[str], Optional[str]]:
        """Test connection to Prowlarr."""
        return await self.search_provider.test_connection()


class GetProwlarrIndexerCountQuery:
    """Query for getting the number of configured indexers."""
    
    def __init__(self, search_provider: TorrentSearchProvider):
        self.search_provider = search_provider
    
    async def execute(self) -> int:
        """
        Get the number of enabled indexers.
        
        Business logic: Only count indexers that are enabled.
        """
        indexers = await self.search_provider.get_indexers()
        return len([i for i in indexers if i.enable])

