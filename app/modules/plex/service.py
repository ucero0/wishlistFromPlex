"""Plex module service layer - business logic and external API integration."""
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set
import httpx
import xml.etree.ElementTree as ET
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.modules.plex.models import PlexUser, WishlistItem, WishlistItemSource, MediaType
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
                    normalized = normalize_api_item(item)
                    if normalized:
                        all_items.append(normalized)
                
                logger.info(f"Fetched {len(all_items)} items from Plex watchlist")
            else:
                logger.error(f"Failed to fetch watchlist: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"Error fetching watchlist: {e}")
    
    return all_items


async def remove_from_watchlist(token: str, rating_key: str) -> bool:
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
    params = {"ratingKey": rating_key}
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            logger.info(f"Removing item {rating_key} from watchlist")
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


async def remove_from_all_user_watchlists(db: Session, rating_key: str) -> Dict:
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
    logger.info(f"Removing item {rating_key} from all active users' watchlists")
    
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
            logger.info(f"Removing item {rating_key} from watchlist for user: {user.name} (ID: {user.id})")
            success = await remove_from_watchlist(user.plex_token, rating_key)
            
            if success:
                successful_removals += 1
                logger.info(f"Successfully removed item {rating_key} from user {user.name}'s watchlist")
            else:
                failed_removals += 1
                error_msg = f"Failed to remove item {rating_key} from user {user.name}'s watchlist"
                logger.warning(error_msg)
                errors.append(error_msg)
                
        except Exception as e:
            failed_removals += 1
            error_msg = f"Error removing item {rating_key} from user {user.name} (ID: {user.id}): {str(e)}"
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


async def check_rating_key_in_library(
    server_url: str,
    token: str,
    rating_key: str
) -> bool:
    """
    Check if a rating key exists in the Plex Media Server library.
    
    Uses the /library/all endpoint with guid parameter to search for the item.
    The response is typically JSON, and if MediaContainer has size >= 1, the item exists.
    
    Args:
        server_url: Plex Media Server URL (e.g., "http://homeserver.local:32400" or "http://plex:32400")
        token: Plex user token
        rating_key: The ratingKey to check (e.g., "5d776824f54112001f5bbdd7" or "plex://movie/5d776824f54112001f5bbdd7")
        
    Returns:
        True if the rating key exists in the library, False otherwise
    """
    # Build guid from rating_key - if not already in plex:// format, assume it's a movie
    guid = rating_key if rating_key.startswith("plex://") else f"plex://movie/{rating_key}"
    
    url = f"{server_url}/library/all"
    headers = {**PLEX_API_HEADERS, "X-Plex-Token": token}
    params = {"guid": guid, "X-Plex-Token": token}
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            logger.debug(f"Checking if rating key {rating_key} (guid: {guid}) exists in library at {server_url}")
            response = await client.get(url, headers=headers, params=params)
            
            if response.status_code == 404:
                logger.debug(f"Rating key {rating_key} not found in library (404)")
                return False
            
            if response.status_code != 200:
                logger.warning(f"Unexpected status code {response.status_code} when checking rating key {rating_key}")
                return False
            
            # Try JSON first (most common response format)
            try:
                data = response.json()
                size = data.get("MediaContainer", {}).get("size", 0)
                found = size >= 1
                logger.info(f"Rating key {rating_key} {'found' if found else 'not found'} in library (JSON, size={size})")
                return found
            except (ValueError, AttributeError, TypeError):
                # Fallback to XML parsing
                try:
                    root = ET.fromstring(response.text.strip())
                    media_container = root.find('MediaContainer')
                    if media_container is not None:
                        size = int(media_container.get('size', '0'))
                        found = size >= 1
                        logger.info(f"Rating key {rating_key} {'found' if found else 'not found'} in library (XML, size={size})")
                        return found
                    logger.debug(f"Rating key {rating_key} not found in library (no MediaContainer in XML)")
                    return False
                except (ET.ParseError, ValueError) as e:
                    logger.error(f"Error parsing response for rating key {rating_key}: {e}")
                    logger.debug(f"Response content (first 200 chars): {response.text[:200]}")
                    return False
                
        except httpx.TimeoutException:
            logger.error(f"Timeout checking rating key {rating_key} in library at {server_url}")
            return False
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error checking rating key {rating_key}: {e.response.status_code} - {e.response.text[:200]}")
            return False
        except Exception as e:
            logger.error(f"Error checking rating key {rating_key} in library: {e}")
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


async def search_plex(token: str, query: str, limit: int = 10) -> List[PlexItemData]:
    """
    Search Plex for media items using direct API calls.
    
    Args:
        token: Plex user token
        query: Search query string
        limit: Maximum number of results
        
    Returns:
        List of matching PlexItemData items
    """
    results: List[PlexItemData] = []
    
    url = f"{PLEX_DISCOVER_API}/library/search"
    headers = {**PLEX_API_HEADERS, "X-Plex-Token": token}
    params = {
        "query": query,
        "limit": limit,
        "searchTypes": "movies,tv",
        "includeMetadata": 1,
        "searchProviders": "discover",
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            logger.info(f"Searching Plex for: {query}")
            response = await client.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                
                media_container = data.get("MediaContainer", {})
                search_results = media_container.get("SearchResults", [])
                
                for result_group in search_results:
                    search_result = result_group.get("SearchResult", [])
                    for item in search_result:
                        metadata = item.get("Metadata")
                        if metadata:
                            normalized = normalize_api_item(metadata)
                            if normalized:
                                results.append(normalized)
                
                logger.info(f"Found {len(results)} results for '{query}'")
            else:
                logger.error(f"Search failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"Error searching Plex: {e}")
    
    return results


def normalize_api_item(item: dict) -> Optional[PlexItemData]:
    """
    Normalize a Plex API JSON response item to our standard format.
    
    Args:
        item: Dictionary from Plex API response
        
    Returns:
        PlexItemData schema with all available metadata, or None if invalid
    """
    try:
        # Get the GUID (required)
        guid = item.get("guid")
        if not guid:
            rating_key = item.get("ratingKey")
            item_type = item.get("type", "movie")
            if rating_key:
                guid = f"plex://{item_type}/{rating_key}"
            else:
                logger.warning(f"Item missing GUID: {item.get('title', 'Unknown')}")
                return None
        
        # Get title (required)
        title = item.get("title")
        if not title:
            logger.warning(f"Item missing title: {guid}")
            return None
        
        # Get year
        year = item.get("year")
        if year:
            try:
                year = int(year)
            except (ValueError, TypeError):
                year = None
        
        # Get ratingKey
        rating_key = item.get("ratingKey")
        if rating_key:
            rating_key = str(rating_key)
        
        # Get media type
        media_type = item.get("type")
        if media_type:
            media_type = media_type.lower()
        
        # Get additional metadata
        summary = item.get("summary")
        thumb = item.get("thumb")
        art = item.get("art")
        content_rating = item.get("contentRating")
        studio = item.get("studio")
        
        return PlexItemData(
            guid=guid,
            rating_key=rating_key,
            title=title,
            year=year,
            media_type=media_type,
            summary=summary,
            thumb=thumb,
            art=art,
            content_rating=content_rating,
            studio=studio,
        )
        
    except Exception as e:
        logger.error(f"Error normalizing API item: {e}")
        return None


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


async def sync_all_users(db: Session) -> Dict:
    """
    Sync watchlists from all active Plex users and merge into shared wishlist.
    
    This function only handles Plex API interactions and database operations.
    For integration with torrent search, use the OrchestrationService.
    
    Args:
        db: Database session
        
    Returns:
        Dictionary with sync summary statistics
    """
    logger.info("Starting sync for all users")
    
    active_users = db.query(PlexUser).filter(PlexUser.active == True).all()
    
    if not active_users:
        logger.warning("No active users found for sync")
        return {
            "users_processed": 0,
            "items_fetched": 0,
            "new_items": 0,
            "updated_items": 0,
            "errors": [],
        }
    
    logger.info(f"Found {len(active_users)} active users")
    
    all_items_by_guid: Dict[str, PlexItemData] = {}
    user_items: Dict[int, Set[str]] = {}
    
    errors: List[str] = []
    total_fetched = 0
    
    # Fetch watchlist for each user
    for user in active_users:
        try:
            logger.info(f"Fetching watchlist for user: {user.name} (ID: {user.id})")
            items = await get_watchlist(user.plex_token)
            
            user_items[user.id] = set()
            for item in items:
                guid = item.guid
                all_items_by_guid[guid] = item
                user_items[user.id].add(guid)
            
            total_fetched += len(items)
            logger.info(f"Fetched {len(items)} items from user {user.name}")
            
        except Exception as e:
            error_msg = f"Error fetching watchlist for user {user.name} (ID: {user.id}): {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)
            continue
    
    # Merge into database
    new_items = 0
    updated_items = 0
    
    for guid, item in all_items_by_guid.items():
        existing_item = db.query(WishlistItem).filter(WishlistItem.guid == guid).first()
        
        if existing_item:
            updated = False
            
            if existing_item.title != item.title:
                existing_item.title = item.title
                updated = True
            if existing_item.year != item.year:
                existing_item.year = item.year
                updated = True
            if existing_item.rating_key != item.rating_key:
                existing_item.rating_key = item.rating_key
                updated = True
            
            new_media_type = parse_media_type(item.media_type)
            if existing_item.media_type != new_media_type:
                existing_item.media_type = new_media_type
                updated = True
            
            if item.summary and existing_item.summary != item.summary:
                existing_item.summary = item.summary
                updated = True
            if item.thumb and existing_item.thumb != item.thumb:
                existing_item.thumb = item.thumb
                updated = True
            if item.art and existing_item.art != item.art:
                existing_item.art = item.art
                updated = True
            if item.content_rating and existing_item.content_rating != item.content_rating:
                existing_item.content_rating = item.content_rating
                updated = True
            if item.studio and existing_item.studio != item.studio:
                existing_item.studio = item.studio
                updated = True
                
            existing_item.last_seen_at = datetime.now(timezone.utc)
            
            if updated:
                updated_items += 1
                logger.debug(f"Updated item: {guid} - {item.title}")
        else:
            new_item = WishlistItem(
                guid=guid,
                rating_key=item.rating_key,
                title=item.title,
                year=item.year,
                media_type=parse_media_type(item.media_type),
                summary=item.summary,
                thumb=item.thumb,
                art=item.art,
                content_rating=item.content_rating,
                studio=item.studio,
                added_at=datetime.now(timezone.utc),
                last_seen_at=datetime.now(timezone.utc),
            )
            db.add(new_item)
            db.flush()
            existing_item = new_item
            new_items += 1
            
            logger.debug(f"Added new item: {guid} - {item.title}")
        
        # Update sources
        for user_id, guids in user_items.items():
            if guid in guids:
                source = db.query(WishlistItemSource).filter(
                    and_(
                        WishlistItemSource.wishlist_item_id == existing_item.id,
                        WishlistItemSource.plex_user_id == user_id,
                    )
                ).first()
                
                if source:
                    source.last_seen_at = datetime.now(timezone.utc)
                else:
                    new_source = WishlistItemSource(
                        wishlist_item_id=existing_item.id,
                        plex_user_id=user_id,
                        first_added_at=datetime.now(timezone.utc),
                        last_seen_at=datetime.now(timezone.utc),
                    )
                    db.add(new_source)
    
    # Commit
    try:
        db.commit()
        logger.info(f"Sync completed: {new_items} new items, {updated_items} updated items")
    except Exception as e:
        db.rollback()
        error_msg = f"Error committing sync: {str(e)}"
        logger.error(error_msg)
        errors.append(error_msg)
        raise
    
    return {
        "users_processed": len(active_users),
        "items_fetched": total_fetched,
        "new_items": new_items,
        "updated_items": updated_items,
        "total_items": len(all_items_by_guid),
        "errors": errors,
        "sync_time": datetime.now(timezone.utc).isoformat(),
    }
