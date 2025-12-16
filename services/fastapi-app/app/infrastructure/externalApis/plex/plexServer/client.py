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
        
        # Log request details (mask token for security)
        from urllib.parse import urlencode
        params_for_log = {k: v if k != "X-Plex-Token" else "***" for k, v in params.items()}
        logger.info(f"Making Plex API request: GET {url}?{urlencode(params_for_log)}")
        logger.debug(f"Request params (token masked): {params_for_log}")
        logger.debug(f"Request headers: {self.plex_api_headers}")
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    url,
                    headers=self.plex_api_headers,
                    params=params,
                )
                logger.debug(f"Plex API response status: {response.status_code}")
                logger.debug(f"Plex API response headers: {dict(response.headers)}")
                
                # Log response body for debugging (first 500 chars to avoid huge logs)
                response_text = response.text
                logger.debug(f"Plex API response body (first 500 chars): {response_text[:500]}")
                
                response.raise_for_status()
                # Log the actual URL that was sent (includes query params with token)
                logger.debug(f"Actual request URL sent: {response.request.url}")
                
                # Parse JSON response
                try:
                    response_json = response.json()
                    size = response_json.get("MediaContainer", {}).get("size", 0)
                    logger.info(f"Successfully parsed Plex API JSON response. MediaContainer size: {size}")
                    return response_json
                except json.JSONDecodeError as json_err:
                    logger.error(f"Failed to parse Plex API JSON response: {str(json_err)}")
                    logger.error(f"Response text: {response_text[:1000]}")
                    raise
        except httpx.HTTPStatusError as e:
            logger.error(f"Plex API HTTP error: {e.response.status_code} - {e.response.text[:500]}")
            logger.error(f"Request URL: {e.request.url}")
            logger.error(f"Request headers: { {k: v if k != 'X-Plex-Token' else '***' for k, v in e.request.headers.items()} }")
            raise
        except httpx.RequestError as e:
            error_type = e.__class__.__name__
            logger.error(f"Plex API request error: {error_type} - {str(e)}")
            # Log the actual request URL if available
            if hasattr(e, 'request') and hasattr(e.request, 'url'):
                logger.error(f"Request URL that failed: {e.request.url}")
            else:
                logger.error(f"Base URL: {url}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Plex API JSON response: {str(e)}")
            logger.error(f"Response text: {response_text[:1000] if 'response_text' in locals() else 'N/A'}")
            raise
