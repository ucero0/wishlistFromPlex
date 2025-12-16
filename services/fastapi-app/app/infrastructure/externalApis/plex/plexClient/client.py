import logging
from typing import Dict, Any
import httpx

logger = logging.getLogger(__name__)

PLEX_DISCOVER_API = "https://discover.provider.plex.tv"

DEFAULT_HEADERS = {
    "Accept": "application/json",
    "X-Plex-Client-Identifier": "plex-wishlist-service",
    "X-Plex-Product": "Plex Wishlist Service",
    "X-Plex-Version": "1.0.0",
}

class PlexWatchlistClient:
    def _headers(self, user_token: str) -> Dict[str, Any]:
        return {**DEFAULT_HEADERS, "X-Plex-Token": user_token}

    async def get_watchlist_raw(self, user_token: str) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{PLEX_DISCOVER_API}/library/sections/watchlist/all",
                headers=self._headers(user_token),
            )
            response.raise_for_status()
            return response.json()

    async def delete_item_raw(self, rating_key: str, user_token: str) -> None:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.put(
                f"{PLEX_DISCOVER_API}/actions/removeFromWatchlist",
                params={"ratingKey": rating_key},
                headers=self._headers(user_token),
            )
            response.raise_for_status()