"""Plex module service layer - business logic and external API integration."""
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set
import httpx
from sqlalchemy.orm import Session
from sqlalchemy import and_
from plexapi.myplex import MyPlexAccount
from plexapi.exceptions import Unauthorized

from app.modules.plex.models import PlexUser, WishlistItem, WishlistItemSource, MediaType
from app.modules.plex.schemas import PlexItemData, PlexAccountInfo

logger = logging.getLogger(__name__)


# ============================================================================
# PLEX API CLIENT
# ============================================================================

def get_plex_account(token: str) -> Optional[MyPlexAccount]:
    """
    Create a MyPlexAccount instance from a token.
    
    Args:
        token: Plex user token
        
    Returns:
        MyPlexAccount instance or None if authentication fails
    """
    try:
        account = MyPlexAccount(token=token)
        return account
    except Unauthorized:
        logger.error("Invalid Plex token (Unauthorized)")
        return None
    except Exception as e:
        logger.error(f"Error creating Plex account: {e}")
        return None


async def get_watchlist(token: str) -> List[PlexItemData]:
    """
    Fetch watchlist from Plex using the plexapi library.
    
    Args:
        token: Plex user token
        
    Returns:
        List of normalized watchlist items as PlexItemData schemas
    """
    account = get_plex_account(token)
    if not account:
        return []
    
    all_items: List[PlexItemData] = []
    
    try:
        logger.info("Fetching watchlist using plexapi")
        watchlist = account.watchlist()
        
        for item in watchlist:
            normalized = normalize_plex_item(item)
            if normalized:
                all_items.append(normalized)
        
        logger.info(f"Fetched {len(all_items)} items from Plex watchlist")
        
    except Exception as e:
        logger.error(f"Error fetching watchlist: {e}")
    
    return all_items


async def remove_from_watchlist(token: str, guid: str) -> bool:
    """
    Remove an item from the Plex account watchlist using its GUID.
    Uses direct API call for efficiency.
    
    Args:
        token: Plex user token
        guid: The GUID of the item to remove
        
    Returns:
        bool: True if successful, False otherwise
    """
    url = "https://discover.provider.plex.tv/actions/removeFromWatchlist"
    
    headers = {
        "X-Plex-Token": token,
        "Accept": "application/json",
    }
    
    params = {"ratingKey": guid}
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            logger.info(f"Removing item {guid} from watchlist")
            response = await client.put(url, headers=headers, params=params)
            
            if response.status_code == 200:
                logger.info(f"Successfully removed item {guid} from watchlist")
                return True
            else:
                logger.error(f"Failed to remove item {guid}: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error removing item {guid} from watchlist: {e}")
            return False


async def add_to_watchlist(token: str, guid: str) -> bool:
    """
    Add an item to the Plex account watchlist using its GUID.
    Uses direct API call for efficiency.
    
    Args:
        token: Plex user token
        guid: The GUID of the item to add
        
    Returns:
        bool: True if successful, False otherwise
    """
    url = "https://discover.provider.plex.tv/actions/addToWatchlist"
    
    headers = {
        "X-Plex-Token": token,
        "Accept": "application/json",
    }
    
    params = {"ratingKey": guid}
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            logger.info(f"Adding item {guid} to watchlist")
            response = await client.put(url, headers=headers, params=params)
            
            if response.status_code == 200:
                logger.info(f"Successfully added item {guid} to watchlist")
                return True
            else:
                logger.error(f"Failed to add item {guid}: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error adding item {guid} to watchlist: {e}")
            return False


def normalize_plex_item(item) -> Optional[PlexItemData]:
    """
    Normalize a plexapi media item to our standard format.
    
    Args:
        item: plexapi media object (Movie, Show, etc.)
        
    Returns:
        PlexItemData schema with all available metadata, or None if invalid
    """
    try:
        # Get the GUID
        guid = getattr(item, 'guid', None)
        if not guid:
            rating_key = getattr(item, 'ratingKey', None)
            item_type = getattr(item, 'type', 'movie')
            if rating_key:
                guid = f"plex://{item_type}/{rating_key}"
            else:
                logger.warning(f"Item missing GUID: {getattr(item, 'title', 'Unknown')}")
                return None
        
        # Get title (required)
        title = getattr(item, 'title', None)
        if not title:
            logger.warning(f"Item missing title: {guid}")
            return None
        
        # Get year
        year = getattr(item, 'year', None)
        if year:
            try:
                year = int(year)
            except (ValueError, TypeError):
                year = None
        
        # Get ratingKey
        rating_key = getattr(item, 'ratingKey', None)
        if rating_key:
            rating_key = str(rating_key)
        
        # Get media type
        media_type = getattr(item, 'type', None)
        if not media_type:
            class_name = item.__class__.__name__.lower()
            if 'movie' in class_name:
                media_type = 'movie'
            elif 'show' in class_name:
                media_type = 'show'
            elif 'season' in class_name:
                media_type = 'season'
            elif 'episode' in class_name:
                media_type = 'episode'
        if media_type:
            media_type = media_type.lower()
        
        # Get additional metadata
        summary = getattr(item, 'summary', None)
        thumb = getattr(item, 'thumb', None)
        art = getattr(item, 'art', None)
        content_rating = getattr(item, 'contentRating', None)
        studio = getattr(item, 'studio', None)
        
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
        logger.error(f"Error normalizing item: {e}")
        return None


async def get_account_info(token: str) -> Optional[PlexAccountInfo]:
    """Get Plex account information."""
    account = get_plex_account(token)
    if not account:
        return None
    
    try:
        return PlexAccountInfo(
            username=account.username,
            email=account.email,
            title=account.title,
            uuid=account.uuid,
        )
    except Exception as e:
        logger.error(f"Error getting account info: {e}")
        return None


async def search_plex(token: str, query: str, limit: int = 10) -> List[PlexItemData]:
    """Search Plex for media items."""
    account = get_plex_account(token)
    if not account:
        return []
    
    results: List[PlexItemData] = []
    
    try:
        logger.info(f"Searching Plex for: {query}")
        search_results = account.searchDiscover(query, limit=limit)
        
        for item in search_results:
            normalized = normalize_plex_item(item)
            if normalized:
                results.append(normalized)
        
        logger.info(f"Found {len(results)} results for '{query}'")
        
    except Exception as e:
        logger.error(f"Error searching Plex: {e}")
    
    return results


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

