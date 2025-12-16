import httpx
from typing import Optional, Dict, Any
from app.core.config import settings
import json
import logging

logger = logging.getLogger(__name__)

PLEX_API_HEADERS = {
    "Accept": "application/json",
    "X-Plex-Client-Identifier": "plex-wishlist-service",
    "X-Plex-Product": "Plex Wishlist Service",
    "X-Plex-Version": "1.0.0",
}

class PlexServerLibraryApiClient:
    """Infrastructure client for Plex library API communication."""

    def __init__(self, token: str):
        self.plex_server_url = settings.plex_server_url
        self.token = token
        self.plex_api_headers = PLEX_API_HEADERS
        self.url_library_search = f"{self.plex_server_url}/library/all"
        logger.debug(f"PlexServerLibraryApiClient initialized with server URL: {self.plex_server_url}")

    def _build_params(self, guid: str, user_token: str, media_type: Optional[int] = None) -> Dict[str, Any]:
        """Build query parameters for Plex API request. Token is included as a query parameter."""
        params = {
            "guid": guid,
            "X-Plex-Token": user_token
        }
        if media_type is not None:
            params["type"] = media_type
        return params

    async def get_library_items_raw(self, user_token: str, guid: str, type: Optional[int] = None) -> Dict[str, Any]:
        """Raw Plex request to search library by GUID.
        
        Args:
            user_token: Plex user token (sent as query parameter X-Plex-Token)
            guid: Media GUID to search for
            type: Optional media type (1=movie, 2=show)
            
        Returns:
            JSON dictionary of the response
        """
        params = self._build_params(guid, user_token, type)
        url = self.url_library_search
        

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                url,
                headers=self.plex_api_headers,
                params=params,
            )
            
            response.raise_for_status()
            # Log the actual URL that was sent (includes query params with token)
            logger.debug(f"Actual request URL sent: {response.request.url}")
            
            response_json = response.json()
            return response_json
                
