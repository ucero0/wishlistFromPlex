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



