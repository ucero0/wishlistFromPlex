import logging
from datetime import datetime, timezone
from typing import Dict, List
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.plex_user import PlexUser
from app.models.wishlist_item import WishlistItem, WishlistItemSource
from app.services.plex_client import get_watchlist

logger = logging.getLogger(__name__)


async def sync_all_users(db: Session) -> Dict:
    """
    Sync watchlists from all active Plex users and merge into shared wishlist.
    
    Args:
        db: Database session
        
    Returns:
        Dictionary with sync summary statistics
    """
    logger.info("Starting sync for all users")
    
    # Fetch all active users
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
    
    all_items_by_uid = {}  # uid -> item data
    user_items = {}  # user_id -> list of uids
    
    errors = []
    total_fetched = 0
    
    # Fetch watchlist for each user
    for user in active_users:
        try:
            logger.info(f"Fetching watchlist for user: {user.name} (ID: {user.id})")
            items = await get_watchlist(user.plex_token)
            
            user_items[user.id] = []
            for item in items:
                uid = item["uid"]
                # Store item (last user's data wins if duplicate, but that's okay)
                all_items_by_uid[uid] = item
                user_items[user.id].append(uid)
            
            total_fetched += len(items)
            logger.info(f"Fetched {len(items)} items from user {user.name}")
            
        except Exception as e:
            error_msg = f"Error fetching watchlist for user {user.name} (ID: {user.id}): {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)
            continue
    
    # Now merge into database
    new_items = 0
    updated_items = 0
    
    for uid, item_data in all_items_by_uid.items():
        # Check if item already exists
        existing_item = db.query(WishlistItem).filter(WishlistItem.uid == uid).first()
        
        if existing_item:
            # Update existing item
            updated = False
            if existing_item.title != item_data["title"]:
                existing_item.title = item_data["title"]
                updated = True
            if existing_item.year != item_data.get("year"):
                existing_item.year = item_data.get("year")
                updated = True
            existing_item.last_seen_at = datetime.now(timezone.utc)
            
            if updated:
                updated_items += 1
                logger.debug(f"Updated item: {uid} - {item_data['title']}")
        else:
            # Create new item
            new_item = WishlistItem(
                uid=uid,
                title=item_data["title"],
                year=item_data.get("year"),
                added_at=datetime.now(timezone.utc),
                last_seen_at=datetime.now(timezone.utc),
            )
            db.add(new_item)
            db.flush()  # Get the ID
            existing_item = new_item
            new_items += 1
            logger.debug(f"Added new item: {uid} - {item_data['title']}")
        
        # Update wishlist_item_sources for all users who have this item
        for user_id, uids in user_items.items():
            if uid in uids:
                # Check if source relationship already exists
                source = db.query(WishlistItemSource).filter(
                    and_(
                        WishlistItemSource.wishlist_item_id == existing_item.id,
                        WishlistItemSource.plex_user_id == user_id,
                    )
                ).first()
                
                if source:
                    # Update last_seen_at
                    source.last_seen_at = datetime.now(timezone.utc)
                else:
                    # Create new source relationship
                    new_source = WishlistItemSource(
                        wishlist_item_id=existing_item.id,
                        plex_user_id=user_id,
                        first_added_at=datetime.now(timezone.utc),
                        last_seen_at=datetime.now(timezone.utc),
                    )
                    db.add(new_source)
    
    # Commit all changes
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
        "total_items": len(all_items_by_uid),
        "errors": errors,
        "sync_time": datetime.now(timezone.utc).isoformat(),
    }

