from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import List, Optional

from app.core.db import get_db
from app.models.wishlist_item import WishlistItem
from app.api.schemas import WishlistItemResponse, WishlistStatsResponse

router = APIRouter(prefix="/api/wishlist", tags=["wishlist"])


@router.get("", response_model=List[WishlistItemResponse])
async def get_wishlist(
    search: Optional[str] = Query(None, description="Search term for title"),
    year: Optional[int] = Query(None, description="Filter by year"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: Session = Depends(get_db),
):
    """Get wishlist items with optional filtering and pagination."""
    query = db.query(WishlistItem)
    
    # Apply filters
    if search:
        query = query.filter(WishlistItem.title.ilike(f"%{search}%"))
    
    if year is not None:
        query = query.filter(WishlistItem.year == year)
    
    # Apply pagination
    items = query.order_by(WishlistItem.added_at.desc()).offset(offset).limit(limit).all()
    
    return [
        WishlistItemResponse(
            id=item.id,
            uid=item.uid,
            title=item.title,
            year=item.year,
            user_name=item.user_name,
            plex_token=item.plex_token,
            rating_key=item.rating_key,
            added_at=item.added_at,
            last_seen_at=item.last_seen_at,
        )
        for item in items
    ]


@router.get("/{uid}", response_model=WishlistItemResponse)
async def get_wishlist_item(uid: str, db: Session = Depends(get_db)):
    """Get a specific wishlist item by uid."""
    item = db.query(WishlistItem).filter(WishlistItem.uid == uid).first()
    if not item:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Wishlist item with uid '{uid}' not found",
        )
    
    return WishlistItemResponse(
        id=item.id,
        uid=item.uid,
        title=item.title,
        year=item.year,
        user_name=item.user_name,
        plex_token=item.plex_token,
        rating_key=item.rating_key,
        added_at=item.added_at,
        last_seen_at=item.last_seen_at,
    )


@router.get("/stats/summary", response_model=WishlistStatsResponse)
async def get_wishlist_stats(db: Session = Depends(get_db)):
    """Get summary statistics about the wishlist."""
    total_items = db.query(func.count(WishlistItem.id)).scalar()
    
    # Count items by year
    year_counts = (
        db.query(WishlistItem.year, func.count(WishlistItem.id))
        .filter(WishlistItem.year.isnot(None))
        .group_by(WishlistItem.year)
        .all()
    )
    
    items_by_year = {str(year): count for year, count in year_counts if year is not None}
    
    return WishlistStatsResponse(
        total_items=total_items or 0,
        items_by_year=items_by_year,
    )


@router.delete("/remove-by-rating-key/{rating_key}")
async def remove_wishlist_item_by_rating_key(rating_key: str, db: Session = Depends(get_db)):
    """
    Remove an item from the watchlist using its ratingKey.
    Looks up the item in the database to find the user's token and removes it from Plex.
    If multiple users have the same item (same ratingKey), it removes for all of them.
    """
    from app.services.plex_client import remove_from_watchlist
    from fastapi import HTTPException, status
    import logging
    
    logger = logging.getLogger(__name__)
    
    # Find all items with this ratingKey
    items = db.query(WishlistItem).filter(WishlistItem.rating_key == rating_key).all()
    
    if not items:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No items found with ratingKey '{rating_key}'",
        )
    
    success_count = 0
    errors = []
    
    for item in items:
        if not item.plex_token:
            logger.warning(f"Item {item.id} (ratingKey: {rating_key}) has no plex_token, skipping")
            continue
            
        try:
            result = await remove_from_watchlist(item.plex_token, rating_key)
            if result:
                success_count += 1
                # Optionally delete from our DB too, or let the next sync handle it
                # For immediate feedback, we can delete from DB
                db.delete(item)
            else:
                errors.append(f"Failed to remove item for user {item.user_name}")
        except Exception as e:
            logger.error(f"Error removing item {rating_key}: {e}")
            errors.append(str(e))
    
    if success_count > 0:
        db.commit()
        return {
            "message": f"Successfully removed item from {success_count} watchlists",
            "errors": errors
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove item. Errors: {'; '.join(errors)}",
        )





