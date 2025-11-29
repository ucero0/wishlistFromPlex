import httpx
import logging
from typing import List, Dict, Optional
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

# Plex Discover API watchlist endpoint
PLEX_WATCHLIST_URL = "https://discover.provider.plex.tv/library/sections/watchlist/all"


async def get_watchlist(token: str) -> List[Dict]:
    """
    Fetch watchlist from Plex Discover API using the specific endpoint.
    
    Args:
        token: Plex user token
        
    Returns:
        List of normalized watchlist items
    """
    headers = {
        "X-Plex-Token": token,
        "Accept": "application/json",
    }
    
    all_items = []
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            logger.info(f"Fetching watchlist from {PLEX_WATCHLIST_URL}")
            response = await client.get(PLEX_WATCHLIST_URL, headers=headers)
            
            if response.status_code == 401:
                logger.error("Invalid Plex token (401)")
                return []
            
            if response.status_code != 200:
                logger.error(f"Plex API error: {response.status_code} - {response.text[:200]}")
                return []
            
            # Parse response
            content_type = response.headers.get("content-type", "")
            items = []
            
            if "json" in content_type:
                try:
                    data = response.json()
                    items = data.get("MediaContainer", {}).get("Metadata", [])
                except Exception as e:
                    logger.error(f"Error parsing JSON response: {e}")
                    return []
            else:
                # Parse XML
                try:
                    root = ET.fromstring(response.text)
                    items = root.findall(".//Video") + root.findall(".//Directory")
                except ET.ParseError as e:
                    logger.error(f"Error parsing XML response: {e}")
                    return []

            for item in items:
                if isinstance(item, dict):
                    normalized = normalize_watchlist_item(item)
                else:
                    normalized = normalize_xml_item(item)
                
                if normalized:
                    all_items.append(normalized)
                    
            logger.info(f"Fetched {len(all_items)} items from Plex Discover API")
            
        except Exception as e:
            logger.error(f"Error fetching watchlist: {e}")
            
    return all_items


async def remove_from_watchlist(token: str, rating_key: str) -> bool:
    """
    Remove an item from the Plex watchlist using its ratingKey.
    
    Args:
        token: Plex user token
        rating_key: The ratingKey of the item to remove
        
    Returns:
        bool: True if successful, False otherwise
    """
    url = f"https://discover.provider.plex.tv/actions/removeFromWatchlist"
    
    headers = {
        "X-Plex-Token": token,
        "Accept": "application/json",
    }
    
    params = {
        "ratingKey": rating_key
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            logger.info(f"Removing item {rating_key} from watchlist")
            # The user requested a PUT method for this action
            response = await client.put(url, headers=headers, params=params)
            
            if response.status_code == 200:
                logger.info(f"Successfully removed item {rating_key} from watchlist")
                return True
            else:
                logger.error(f"Failed to remove item {rating_key}: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error removing item {rating_key} from watchlist: {e}")
            return False


def normalize_watchlist_item(item: Dict) -> Optional[Dict]:
    """
    Normalize a Plex API watchlist item to our standard format.
    
    Args:
        item: Raw item from Plex API (dict)
        
    Returns:
        Normalized dict with uid, title, year, or None if invalid
    """
    try:
        # Extract GUID (uid) - this is the stable identifier
        guid = item.get("guid") or item.get("GUID") or item.get("ratingKey")
        if not guid:
            # Try to construct from ratingKey if available
            rating_key = item.get("ratingKey")
            if rating_key:
                guid = f"plex://{item.get('type', 'movie')}/{rating_key}"
            else:
                logger.warning(f"Item missing GUID: {item.get('title', 'Unknown')}")
                return None
        
        # Extract title
        title = item.get("title") or item.get("Title", "") or item.get("name", "")
        if not title:
            logger.warning(f"Item missing title: {guid}")
            return None
        
        # Extract year
        year = item.get("year") or item.get("Year") or item.get("originallyAvailableAt")
        if year:
            try:
                # If it's a date string, extract year
                if isinstance(year, str) and "-" in year:
                    year = int(year.split("-")[0])
                else:
                    year = int(year)
            except (ValueError, TypeError):
                year = None
        
        # Extract ratingKey
        rating_key = item.get("ratingKey")
        if not rating_key:
            logger.warning(f"Item missing ratingKey: {title}")
            return None

        return {
            "uid": guid,
            "title": title,
            "year": year,
            "rating_key": rating_key,
        }
    except Exception as e:
        logger.error(f"Error normalizing item: {e}")
        return None


def normalize_xml_item(item: ET.Element) -> Optional[Dict]:
    """
    Normalize a Plex API watchlist item from XML to our standard format.
    
    Args:
        item: XML element from Plex API
        
    Returns:
        Normalized dict with uid, title, year, or None if invalid
    """
    try:
        # Extract GUID
        guid = item.get("guid") or item.get("ratingKey")
        if not guid:
            rating_key = item.get("ratingKey")
            if rating_key:
                item_type = item.get("type", "movie")
                guid = f"plex://{item_type}/{rating_key}"
            else:
                logger.warning(f"XML item missing GUID")
                return None
        
        # Extract title
        title = item.get("title") or item.get("name", "")
        if not title:
            logger.warning(f"XML item missing title: {guid}")
            return None
        
        # Extract year
        year = item.get("year") or item.get("originallyAvailableAt")
        if year:
            try:
                if isinstance(year, str) and "-" in year:
                    year = int(year.split("-")[0])
                else:
                    year = int(year)
            except (ValueError, TypeError):
                year = None
        
        # Extract ratingKey
        rating_key = item.get("ratingKey")
        if not rating_key:
            logger.warning(f"Item missing ratingKey: {title}")
            return None

        return {
            "uid": guid,
            "title": title,
            "year": year,
            "rating_key": rating_key,
        }
    except Exception as e:
        logger.error(f"Error normalizing XML item: {e}")
        return None
