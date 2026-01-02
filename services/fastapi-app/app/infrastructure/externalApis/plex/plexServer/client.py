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
    
    async def partial_scan_library_raw(
        self, 
        user_token: str, 
        section_id: int, 
        folder_path: str
    ) -> bool:
        """
        Trigger a partial scan of a specific folder in the Plex library.
        
        This is useful when you've added a new file to a folder and don't want to scan
        the entire library. The path must point to a folder, not a file.
        
        Args:
            user_token: Plex user token (sent as query parameter X-Plex-Token)
            section_id: Library section ID (e.g., 1 for movies, 2 for TV shows)
            folder_path: Absolute path to the folder to scan (will be URL encoded)
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            httpx.HTTPStatusError: If the HTTP request fails
        """
        # Build the endpoint URL
        url = f"{self.plex_server_url}/library/sections/{section_id}/refresh"
        
        # Build query parameters with URL-encoded path
        params = {
            "X-Plex-Token": user_token,
            "path": folder_path  # httpx will automatically URL encode this
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    url,
                    headers=self.plex_api_headers,
                    params=params,
                )
                
                response.raise_for_status()
                logger.info(
                    f"Partial scan triggered for section {section_id}, "
                    f"path: {folder_path}"
                )
                logger.debug(f"Partial scan request URL: {response.request.url}")
                return True
        except httpx.HTTPStatusError as e:
            logger.error(
                f"Failed to trigger partial scan for section {section_id}, "
                f"path: {folder_path}. Status: {e.response.status_code}, "
                f"Response: {e.response.text}"
            )
            raise
        except Exception as e:
            logger.error(
                f"Error triggering partial scan for section {section_id}, "
                f"path: {folder_path}: {e}"
            )
            raise
                
