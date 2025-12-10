"""Plex module API routes."""
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime, timezone
import logging

from app.core.db import get_db
from app.core.security import get_api_key, mask_token
from app.modules.plex.models import PlexUser, WishlistItem, MediaType
from app.modules.plex.schemas import (
    PlexUserCreate,
    PlexUserUpdate,
    PlexUserResponse,
    WishlistItemResponse,
    WishlistStatsResponse,
    SyncResponse,
)

logger = logging.getLogger(__name__)

from app.modules.plex.constants import MODULE_PREFIX, USERS_PREFIX, WISHLIST_PREFIX, SYNC_PREFIX

# Main router that combines all sub-routers
router = APIRouter(tags=[MODULE_PREFIX.strip("/")])

# Sub-routers
users_router = APIRouter(prefix=USERS_PREFIX, tags=["users"])
wishlist_router = APIRouter(prefix=WISHLIST_PREFIX, tags=["wishlist"])
sync_router = APIRouter(prefix=SYNC_PREFIX, tags=["sync"])


# ============================================================================
# USER ROUTES
# ============================================================================

@users_router.post("", response_model=PlexUserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: PlexUserCreate,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key),
):
    """Create a new Plex user entry."""
    existing = db.query(PlexUser).filter(PlexUser.name == user_data.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User with name '{user_data.name}' already exists",
        )
    
    new_user = PlexUser(
        name=user_data.name,
        plex_token=user_data.token,
        active=True,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return PlexUserResponse(
        id=new_user.id,
        name=new_user.name,
        token_masked=mask_token(new_user.plex_token),
        active=new_user.active,
        created_at=new_user.created_at,
        updated_at=new_user.updated_at,
    )


@users_router.get("", response_model=List[PlexUserResponse])
async def list_users(db: Session = Depends(get_db)):
    """List all Plex users (tokens are masked)."""
    users = db.query(PlexUser).all()
    return [
        PlexUserResponse(
            id=user.id,
            name=user.name,
            token_masked=mask_token(user.plex_token),
            active=user.active,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
        for user in users
    ]


@users_router.get("/{user_id}", response_model=PlexUserResponse)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    """Get a specific user by ID."""
    user = db.query(PlexUser).filter(PlexUser.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found",
        )
    
    return PlexUserResponse(
        id=user.id,
        name=user.name,
        token_masked=mask_token(user.plex_token),
        active=user.active,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@users_router.patch("/{user_id}", response_model=PlexUserResponse)
async def update_user(
    user_id: int,
    user_data: PlexUserUpdate,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key),
):
    """Update a user's name or active status."""
    user = db.query(PlexUser).filter(PlexUser.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found",
        )
    
    if user_data.name is not None:
        existing = db.query(PlexUser).filter(
            PlexUser.name == user_data.name,
            PlexUser.id != user_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User with name '{user_data.name}' already exists",
            )
        user.name = user_data.name
    
    if user_data.active is not None:
        user.active = user_data.active
    
    db.commit()
    db.refresh(user)
    
    return PlexUserResponse(
        id=user.id,
        name=user.name,
        token_masked=mask_token(user.plex_token),
        active=user.active,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@users_router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key),
):
    """Soft delete a user (set active=False)."""
    user = db.query(PlexUser).filter(PlexUser.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found",
        )
    
    user.active = False
    db.commit()
    return None


# ============================================================================
# WISHLIST ROUTES
# ============================================================================

def serialize_wishlist_item(item: WishlistItem) -> WishlistItemResponse:
    """Serialize a WishlistItem to response format."""
    return WishlistItemResponse(
        id=item.id,
        guid=item.guid,
        rating_key=item.rating_key,
        title=item.title,
        year=item.year,
        media_type=item.media_type.value if item.media_type else None,
        summary=item.summary,
        thumb=item.thumb,
        art=item.art,
        content_rating=item.content_rating,
        studio=item.studio,
        added_at=item.added_at,
        last_seen_at=item.last_seen_at,
    )


@wishlist_router.get("", response_model=List[WishlistItemResponse])
async def get_wishlist(
    search: Optional[str] = Query(None, description="Search term for title"),
    year: Optional[int] = Query(None, description="Filter by year"),
    media_type: Optional[str] = Query(None, description="Filter by media type (movie, show)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: Session = Depends(get_db),
):
    """Get wishlist items with optional filtering and pagination."""
    query = db.query(WishlistItem)
    
    if search:
        query = query.filter(WishlistItem.title.ilike(f"%{search}%"))
    
    if year is not None:
        query = query.filter(WishlistItem.year == year)
    
    if media_type:
        try:
            # MediaType enum uses lowercase values (movie, show, etc.)
            mt = MediaType(media_type.lower())
            query = query.filter(WishlistItem.media_type == mt)
        except ValueError:
            pass
    
    items = query.order_by(WishlistItem.added_at.desc()).offset(offset).limit(limit).all()
    return [serialize_wishlist_item(item) for item in items]


@wishlist_router.get("/stats/summary", response_model=WishlistStatsResponse)
async def get_wishlist_stats(db: Session = Depends(get_db)):
    """Get summary statistics about the wishlist."""
    total_items = db.query(func.count(WishlistItem.id)).scalar()
    
    year_counts = (
        db.query(WishlistItem.year, func.count(WishlistItem.id))
        .filter(WishlistItem.year.isnot(None))
        .group_by(WishlistItem.year)
        .all()
    )
    items_by_year = {str(year): count for year, count in year_counts if year is not None}
    
    type_counts = (
        db.query(WishlistItem.media_type, func.count(WishlistItem.id))
        .filter(WishlistItem.media_type.isnot(None))
        .group_by(WishlistItem.media_type)
        .all()
    )
    items_by_type = {mt.value if mt else "unknown": count for mt, count in type_counts}
    
    return WishlistStatsResponse(
        total_items=total_items or 0,
        items_by_year=items_by_year,
        items_by_type=items_by_type,
    )


@wishlist_router.get("/{guid:path}", response_model=WishlistItemResponse)
async def get_wishlist_item(guid: str, db: Session = Depends(get_db)):
    """Get a specific wishlist item by GUID."""
    item = db.query(WishlistItem).filter(WishlistItem.guid == guid).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Wishlist item with guid '{guid}' not found",
        )
    return serialize_wishlist_item(item)


@wishlist_router.delete("/remove/{guid:path}")
async def remove_wishlist_item(guid: str, db: Session = Depends(get_db)):
    """Remove an item from the watchlist using its GUID."""
    from app.modules.plex.service import remove_from_watchlist
    
    item = db.query(WishlistItem).filter(WishlistItem.guid == guid).first()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No item found with guid '{guid}'",
        )
    
    if not item.rating_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Item has no rating_key - cannot remove from Plex",
        )
    
    success_count = 0
    errors = []
    
    if not item.sources:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No users associated with this item",
        )
    
    for source in item.sources:
        if source.plex_user and source.plex_user.plex_token:
            try:
                # Use rating_key for Plex API, not GUID
                result = await remove_from_watchlist(source.plex_user.plex_token, item.rating_key)
                if result:
                    success_count += 1
            except Exception as e:
                logger.error(f"Error removing item {item.rating_key} for user {source.plex_user.name}: {e}")
                errors.append(f"User {source.plex_user.name}: {str(e)}")
    
    if success_count > 0:
        db.delete(item)
        db.commit()
        return {
            "message": f"Successfully removed item from {success_count} watchlist(s)",
            "guid": guid,
            "rating_key": item.rating_key,
            "errors": errors if errors else None
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove item. Errors: {'; '.join(errors) if errors else 'No token available'}",
        )


@wishlist_router.delete("/remove-by-rating-key/{rating_key}")
async def remove_wishlist_item_by_rating_key(rating_key: str, db: Session = Depends(get_db)):
    """Remove an item from the watchlist using its ratingKey."""
    from app.modules.plex.service import remove_from_watchlist
    
    items = db.query(WishlistItem).filter(WishlistItem.rating_key == rating_key).all()
    
    if not items:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No items found with ratingKey '{rating_key}'",
        )
    
    success_count = 0
    errors = []
    
    for item in items:
        if item.rating_key and item.sources:
            for source in item.sources:
                if source.plex_user and source.plex_user.plex_token:
                    try:
                        # Use rating_key for Plex API
                        result = await remove_from_watchlist(source.plex_user.plex_token, item.rating_key)
                        if result:
                            success_count += 1
                            break
                    except Exception as e:
                        logger.error(f"Error removing item {rating_key}: {e}")
                        errors.append(str(e))
            
            if success_count > 0:
                db.delete(item)
    
    if success_count > 0:
        db.commit()
        return {
            "message": f"Successfully removed item from {success_count} watchlist(s)",
            "rating_key": rating_key,
            "errors": errors if errors else None
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove item. Errors: {'; '.join(errors) if errors else 'No valid items found'}",
        )


@wishlist_router.delete("/delete-all", status_code=status.HTTP_200_OK)
async def delete_all_wishlist_items(
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key),
    confirm: bool = Query(False, description="Must be True to confirm deletion"),
):
    """
    Delete all wishlist items from the database.
    
    WARNING: This permanently deletes all wishlist items from the database.
    It does NOT remove them from Plex watchlists - it only removes them from local storage.
    
    Requires confirmation via query parameter: ?confirm=true
    """
    if not confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Deletion requires confirmation. Add ?confirm=true to the URL.",
        )
    
    # Get count before deletion
    total_count = db.query(func.count(WishlistItem.id)).scalar()
    
    if total_count == 0:
        return {
            "message": "No items to delete",
            "deleted_count": 0,
        }
    
    # Delete all items (cascade will handle related sources)
    deleted_count = db.query(WishlistItem).delete()
    db.commit()
    
    logger.warning(f"Deleted {deleted_count} wishlist items from database (requested by API)")
    
    return {
        "message": f"Successfully deleted {deleted_count} wishlist item(s) from database",
        "deleted_count": deleted_count,
        "note": "Items were removed from local database only. They may still exist in Plex watchlists.",
    }


# ============================================================================
# TEST ROUTES
# ============================================================================

@router.get("/test/check-in-library", dependencies=[Depends(get_api_key)])
async def test_check_rating_key_in_library(
    rating_key: str = Query(..., description="Rating key to check (e.g., '5d776824f54112001f5bbdd7')"),
    server_url: str = Query(..., description="Plex Media Server URL (e.g., 'http://plex:32400' or 'http://homeserver.local:32400')"),
    token: Optional[str] = Query(None, description="Plex user token (optional, will use first active user if not provided)"),
    db: Session = Depends(get_db),
):
    """
    Test endpoint to check if a rating key exists in the Plex Media Server library.
    
    This is a testing/debugging endpoint to verify the check_rating_key_in_library function.
    """
    from app.modules.plex.service import check_rating_key_in_library
    
    # If token not provided, try to get from first active user
    if not token:
        user = db.query(PlexUser).filter(PlexUser.active == True).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No token provided and no active users found in database",
            )
        token = user.plex_token
        logger.info(f"Using token from active user: {user.name}")
    
    try:
        exists = await check_rating_key_in_library(
            server_url=server_url,
            token=token,
            rating_key=rating_key
        )
        
        return {
            "rating_key": rating_key,
            "server_url": server_url,
            "exists_in_library": exists,
            "message": f"Rating key {'found' if exists else 'not found'} in library"
        }
    except Exception as e:
        logger.error(f"Error checking rating key in library: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error checking rating key: {str(e)}",
        )


# ============================================================================
# SYNC ROUTES
# ============================================================================

_last_sync_status = None


@sync_router.post("", response_model=SyncResponse)
async def trigger_sync(
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key),
):
    """Trigger a manual sync of all active Plex users' watchlists."""
    global _last_sync_status
    from app.modules.plex.service import sync_all_users
    
    try:
        result = await sync_all_users(db)
        _last_sync_status = result
        return SyncResponse(**result)
    except Exception as e:
        error_result = {
            "users_processed": 0,
            "items_fetched": 0,
            "new_items": 0,
            "updated_items": 0,
            "total_items": 0,
            "errors": [str(e)],
            "sync_time": datetime.now(timezone.utc).isoformat(),
        }
        _last_sync_status = error_result
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync failed: {str(e)}",
        )


@sync_router.get("/status", response_model=SyncResponse)
async def get_sync_status():
    """Get the status of the last sync operation."""
    global _last_sync_status
    
    if _last_sync_status is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No sync has been performed yet",
        )
    
    return SyncResponse(**_last_sync_status)


# ============================================================================
# INCLUDE SUB-ROUTERS
# ============================================================================

router.include_router(users_router)
router.include_router(wishlist_router)
router.include_router(sync_router)

