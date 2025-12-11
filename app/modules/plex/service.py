"""Plex module service layer - business logic and external API integration."""
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set
import httpx
import xml.etree.ElementTree as ET
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.modules.plex.models import PlexUser,MediaType
from app.modules.plex.schemas import PlexItemData, PlexAccountInfo

logger = logging.getLogger(__name__)

# Plex API base URLs
PLEX_DISCOVER_API = "https://discover.provider.plex.tv"
PLEX_API_HEADERS = {
    "Accept": "application/json",
    "X-Plex-Client-Identifier": "plex-wishlist-service",
    "X-Plex-Product": "Plex Wishlist Service",
    "X-Plex-Version": "1.0.0",
}


# ============================================================================
# PLEX API CLIENT
# ============================================================================

async def verify_token(token: str) -> bool:
    """
    Verify if a Plex token is valid.
    
    Args:
        token: Plex user token
        
    Returns:
        True if valid, False otherwise
    """
    url = "https://plex.tv/api/v2/user"
    headers = {**PLEX_API_HEADERS, "X-Plex-Token": token}
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(url, headers=headers)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Error verifying token: {e}")
            return False


async def get_account_info(token: str) -> Optional[PlexAccountInfo]:
    """
    Get Plex account information using direct API call.
    
    Args:
        token: Plex user token
        
    Returns:
        PlexAccountInfo with account details, or None if failed
    """
    url = "https://plex.tv/api/v2/user"
    headers = {**PLEX_API_HEADERS, "X-Plex-Token": token}
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                return PlexAccountInfo(
                    username=data.get("username", ""),
                    email=data.get("email"),
                    title=data.get("title"),
                    uuid=data.get("uuid", ""),
                )
            else:
                logger.error(f"Failed to get account info: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            return None
async def get_watchlist(token: str) -> List[PlexItemData]:
    """
    Fetch watchlist from Plex using direct API calls.
    
    Args:
        token: Plex user token
        
    Returns:
        List of normalized watchlist items as PlexItemData schemas
    """
    all_items: List[PlexItemData] = []
    
    url = f"{PLEX_DISCOVER_API}/library/sections/watchlist/all"
    headers = {**PLEX_API_HEADERS, "X-Plex-Token": token}
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            logger.info("Fetching watchlist from Plex Discover API")
            response = await client.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                media_container = data.get("MediaContainer", {})
                metadata_list = media_container.get("Metadata", [])
                
                for item in metadata_list:
                    plexItem = PlexItemData(**item)
                    all_items.append(plexItem)
                return all_items
            else:
                logger.error(f"Failed to fetch watchlist: {response.status_code} - {response.text}")
                return []
        except Exception as e:
            logger.error(f"Error fetching watchlist: {e}")
            return []
def is_item_in_watchlist(items: List[PlexItemData], guid: str) -> bool:
    """
    Check if an item is in the watchlist.
    
    Args:
        items: List of PlexItemData items
        guid: The guid of the item to check (e.g., "plex://movie/5d776d1847dd6e001f6f002f")
    """
    return any(item.guid == guid for item in items)
async def get_watchlistAllUsers(db: Session) -> List[PlexItemData]:
    """
    Get the watchlist from all active Plex users.
    
    Args:
        db: Database session
    """
    active_users = db.query(PlexUser).filter(PlexUser.active == True).all()
    all_items: List[PlexItemData] = []
    for user in active_users:
        items = await get_watchlist(user.plex_token)
        for item in items:
            if not is_item_in_watchlist(all_items, item.guid):
                all_items.append(item)
    return all_items

async def remove_from_watchlist(token: str, ratingKey: str) -> bool:
    """
    Remove an item from the Plex account watchlist using its ratingKey.
    
    Args:
        token: Plex user token
        rating_key: The ratingKey of the item to remove (e.g., "5d776d1847dd6e001f6f002f")
        
    Returns:
        bool: True if successful, False otherwise
    """
    url = f"{PLEX_DISCOVER_API}/actions/removeFromWatchlist"
    headers = {**PLEX_API_HEADERS, "X-Plex-Token": token}
    params = {"ratingKey": ratingKey}
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            logger.info(f"Removing item {ratingKey} from watchlist")
            response = await client.put(url, headers=headers, params=params)
            
            if response.status_code == 200:
                logger.info(f"Successfully removed item {ratingKey} from watchlist")
                return True
            else:
                logger.error(f"Failed to remove item {ratingKey}: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error removing item {ratingKey} from watchlist: {e}")
            return False


async def remove_from_all_user_watchlists(db: Session, ratingKey: str) -> Dict:
    """
    Remove an item from all active users' watchlists.
    
    Args:
        db: Database session
        rating_key: The ratingKey of the item to remove (e.g., "5d776d1847dd6e001f6f002f")
        
    Returns:
        Dictionary with removal summary statistics:
        - users_processed: Number of users processed
        - successful_removals: Number of successful removals
        - failed_removals: Number of failed removals
        - errors: List of error messages
    """
    logger.info(f"Removing item {ratingKey} from all active users' watchlists")
    
    active_users = db.query(PlexUser).filter(PlexUser.active == True).all()
    
    if not active_users:
        logger.warning("No active users found")
        return {
            "users_processed": 0,
            "successful_removals": 0,
            "failed_removals": 0,
            "errors": ["No active users found"],
        }
    
    logger.info(f"Found {len(active_users)} active users")
    
    successful_removals = 0
    failed_removals = 0
    errors: List[str] = []
    
    # Remove from each user's watchlist
    for user in active_users:
        try:
            logger.info(f"Removing item {ratingKey} from watchlist for user: {user.name} (ID: {user.id})")
            success = await remove_from_watchlist(user.plex_token, ratingKey)
            
            if success:
                successful_removals += 1
                logger.info(f"Successfully removed item {ratingKey} from user {user.name}'s watchlist")
            else:
                failed_removals += 1
                error_msg = f"Failed to remove item {ratingKey} from user {user.name}'s watchlist"
                logger.warning(error_msg)
                errors.append(error_msg)
                
        except Exception as e:
            failed_removals += 1
            error_msg = f"Error removing item {ratingKey} from user {user.name} (ID: {user.id}): {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)
            continue
    
    logger.info(
        f"Removal completed: {successful_removals} successful, {failed_removals} failed "
        f"out of {len(active_users)} users"
    )
    
    return {
        "users_processed": len(active_users),
        "successful_removals": successful_removals,
        "failed_removals": failed_removals,
        "errors": errors,
    }


async def is_item_in_plexLibrary(
    guid: str,
    token: Optional[str] = None,
    server_url: Optional[str] = None
) -> bool:
    """
    Check if a specific GUID exists in the Plex Media Server library.

    Uses the /library/all endpoint with the guid parameter.

    Args:
        guid: The GUID to check (e.g., "plex://movie/5d776824f54112001f5bbdd7")
        token: Plex user token (required)
        server_url: Plex Media Server URL (defaults to "http://localhost:32400")

    Returns:
        True if the guid exists in the library, False otherwise.
    """
    if not token:
        logger.warning("Token is required to check if item is in Plex library")
        return False

    # Default server URL if not provided and strip trailing slash
    base_url = (server_url or "http://homeserver.local:32400").rstrip("/")
    url = f"{base_url}/library/all"
    
    # Force JSON response using Accept header
    headers = {
        **PLEX_API_HEADERS,    
    }
    
    params = {"guid": guid,"X-Plex-Token": token}

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            # logger.debug(f"Checking if guid {guid} exists in library at {base_url}")
            response = await client.get(url, headers=headers, params=params)

            if response.status_code == 404:
                return False
            elif response.status_code == 401:
                logger.error(f"Unauthorized to check if guid {guid} exists in library: {response.text}")
                return False

            response.raise_for_status() # Raises exception for 4xx/5xx errors

            data = response.json()
            
            # Plex returns a 'MediaContainer'; we check if it has a size > 0
            size = data.get("MediaContainer", {}).get("size", 0)
            found = size >= 1
            
            if found:
                logger.info(f"Guid {guid} found in library.")
            
            return found

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error checking guid {guid}: {e.response.status_code}")
            return False
        except (httpx.RequestError, ValueError) as e:
            # ValueError covers JSON decoding errors
            logger.error(f"Connection or parsing error for guid {guid}: {e}")
            return False
        except Exception as e:
            logger.exception(f"Unexpected error checking guid {guid}")
            return False


async def add_to_watchlist(token: str, rating_key: str) -> bool:
    """
    Add an item to the Plex account watchlist using its ratingKey.
    
    Args:
        token: Plex user token
        rating_key: The ratingKey of the item to add (e.g., "5d776d1847dd6e001f6f002f")
        
    Returns:
        bool: True if successful, False otherwise
    """
    url = f"{PLEX_DISCOVER_API}/actions/addToWatchlist"
    headers = {**PLEX_API_HEADERS, "X-Plex-Token": token}
    params = {"ratingKey": rating_key}
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            logger.info(f"Adding item {rating_key} to watchlist")
            response = await client.put(url, headers=headers, params=params)
            
            if response.status_code == 200:
                logger.info(f"Successfully added item {rating_key} to watchlist")
                return True
            else:
                logger.error(f"Failed to add item {rating_key}: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error adding item {rating_key} to watchlist: {e}")
            return False


# ============================================================================
# SYNC SERVICE
# ============================================================================

def parse_media_type(media_type_str: Optional[str]) -> Optional[MediaType]:
    """Convert string media type to MediaType enum."""
    if not media_type_str:
        return None
    
    media_type_map = {
        "movie": MediaType.MOVIE,
        "show": MediaType.SHOW,
        "season": MediaType.SEASON,
        "episode": MediaType.EPISODE,
    }
    return media_type_map.get(media_type_str.lower())


async def get_watchlist_items_not_in_plexLibrary(db: Session,remove_from_watchlist: bool = False) -> List[PlexItemData]:
    """
    Get all watchlist items that are not in the plexLibrary.
    
    Args:
        db: Database session
        remove_from_watchlist: If True, remove the item from the watchlist if it is in the plexLibrary
    """
    logger.info("Getting all watchlist items that are not in the plexLibrary")
    
    active_users = db.query(PlexUser).filter(PlexUser.active == True).all()
    
    if not active_users:
        return []
    
    logger.info(f"Found {len(active_users)} active users")
    items_not_in_plexLibrary = []
    for user in active_users:
        items = await get_watchlist(user.plex_token)
        for item in items:
            addItem = True
            #if item is already in plexLibrary, remove from watchlist
            if await is_item_in_plexLibrary(item.guid, token=user.plex_token):
                if remove_from_watchlist:
                    await remove_from_watchlist(user.plex_token, item.ratingKey)
                    addItem = False
   
            #else add to watchlist if not already in watchlist
            if addItem:
                if not is_item_in_watchlist(items_not_in_plexLibrary, item.guid):
                    items_not_in_plexLibrary.append(item)
            
    return items_not_in_plexLibrary
