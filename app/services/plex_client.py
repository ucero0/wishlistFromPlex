import httpx
import logging
from typing import List, Dict, Optional
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

# Plex Discover API base URL
PLEX_DISCOVER_BASE = "https://discover.provider.plex.tv"


async def get_watchlist(token: str) -> List[Dict]:
    """
    Fetch watchlist from Plex Discover API for a given token.
    
    Args:
        token: Plex user token
        
    Returns:
        List of normalized watchlist items with uid (GUID), title, and year
        
    Raises:
        HTTPException: For API errors (401, 429, etc.)
    """
    headers = {
        "X-Plex-Token": token,
        "Accept": "application/json",
    }
    
    all_items = []
    page = 1
    page_size = 50
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        while True:
            try:
                # Plex Discover API endpoint for watchlist
                url = f"{PLEX_DISCOVER_BASE}/v2/watchlist"
                params = {
                    "page": page,
                    "pageSize": page_size,
                }
                
                response = await client.get(url, headers=headers, params=params)
                
                # Handle different status codes
                if response.status_code == 401:
                    logger.error(f"Invalid Plex token (401)")
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid Plex token. Please check your token.",
                    )
                elif response.status_code == 429:
                    logger.warning("Rate limited by Plex API (429)")
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail="Rate limited by Plex API. Please try again later.",
                    )
                elif response.status_code != 200:
                    logger.error(f"Plex API error: {response.status_code} - {response.text}")
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail=f"Plex API returned error: {response.status_code}",
                    )
                
                data = response.json()
                
                # Extract items from response
                # Plex API structure may vary, adjust based on actual response
                items = data.get("MediaContainer", {}).get("Metadata", [])
                
                if not items:
                    break
                
                # Normalize items
                for item in items:
                    normalized = normalize_watchlist_item(item)
                    if normalized:
                        all_items.append(normalized)
                
                # Check if there are more pages
                if len(items) < page_size:
                    break
                    
                page += 1
                
            except httpx.TimeoutException:
                logger.error("Timeout connecting to Plex API")
                raise HTTPException(
                    status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                    detail="Timeout connecting to Plex API.",
                )
            except httpx.RequestError as e:
                logger.error(f"Network error connecting to Plex API: {e}")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Unable to connect to Plex API.",
                )
    
    logger.info(f"Fetched {len(all_items)} items from Plex watchlist")
    return all_items


def normalize_watchlist_item(item: Dict) -> Optional[Dict]:
    """
    Normalize a Plex API watchlist item to our standard format.
    
    Args:
        item: Raw item from Plex API
        
    Returns:
        Normalized dict with uid, title, year, or None if invalid
    """
    try:
        # Extract GUID (uid) - this is the stable identifier
        guid = item.get("guid") or item.get("GUID")
        if not guid:
            logger.warning(f"Item missing GUID: {item.get('title', 'Unknown')}")
            return None
        
        # Extract title
        title = item.get("title") or item.get("Title", "")
        if not title:
            logger.warning(f"Item missing title: {guid}")
            return None
        
        # Extract year
        year = item.get("year") or item.get("Year")
        if year:
            try:
                year = int(year)
            except (ValueError, TypeError):
                year = None
        
        return {
            "uid": guid,
            "title": title,
            "year": year,
        }
    except Exception as e:
        logger.error(f"Error normalizing item: {e}")
        return None



