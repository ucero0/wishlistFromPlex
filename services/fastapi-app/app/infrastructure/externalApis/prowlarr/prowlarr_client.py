"""Prowlarr API client."""
import logging
from typing import Optional, Dict, Any, List
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class ProwlarrClient:
    """Client for interacting with Prowlarr API."""

    def __init__(self):
        self.base_url = f"http://{settings.prowlarr_host}:{settings.prowlarr_port}"
        self.headers = {
            "Content-Type": "application/json",
            "X-Api-Key": settings.prowlarr_api_key
        }

    async def test_connection(self) -> tuple[bool, Optional[str], Optional[str]]:
        """Test connection to Prowlarr."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/system/status",
                    headers=self.headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return True, data.get("version"), None
                else:
                    return False, None, f"HTTP {response.status_code}: {response.text[:200]}"
        except Exception as e:
            return False, None, str(e)

    async def get_indexer_count(self) -> int:
        """Get the number of configured indexers."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/indexer",
                    headers=self.headers
                )
                
                if response.status_code == 200:
                    indexers = response.json()
                    return len([i for i in indexers if i.get("enable", False)])
                return 0
        except Exception:
            return 0

    async def get_indexer_by_id(self, indexer_id: int) -> Optional[Dict[str, Any]]:
        """Get indexer details by ID."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/indexer",
                    headers=self.headers
                )
                
                if response.status_code == 200:
                    indexers = response.json()
                    for indexer in indexers:
                        if indexer.get("id") == indexer_id:
                            return indexer
                return None
        except Exception:
            return None

    async def search(self, query: str, categories: str = "2000") -> List[Dict[str, Any]]:
        """
        Search Prowlarr for torrents.
        
        Args:
            query: Search query string
            categories: Category string (2000 for movies, 5000 for TV)
            
        Returns:
            List of raw search results from Prowlarr
        """
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/search",
                    headers=self.headers,
                    params={
                        "query": query,
                        "categories": categories,
                        "type": "search",
                    }
                )
                
                response.raise_for_status()
                api_response_data = response.json()
                
                if isinstance(api_response_data, list):
                    return api_response_data
                else:
                    logger.warning(f"Unexpected Prowlarr response format: {type(api_response_data)}")
                    return []
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Prowlarr API HTTP error: {e.response.status_code} - {e.response.text[:200]}")
            return []
        except Exception as e:
            logger.error(f"Prowlarr search exception: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return []

    async def send_to_download_client(self, guid: str, indexer_id: int) -> bool:
        """
        Send torrent to download client via Prowlarr.
        
        Args:
            guid: Torrent GUID (magnet link or URL)
            indexer_id: Indexer ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/search",
                    headers=self.headers,
                    json={"guid": guid, "indexerId": indexer_id}
                )
                if response.status_code == 200:
                    return True
                else:
                    logger.error(f"Error sending torrent to client downloader: {response.text}")
                    return False
        except Exception as e:
            logger.error(f"Error sending torrent to client downloader: {e}")
            return False

