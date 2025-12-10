"""Plex module API routes."""
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
import logging

from app.core.db import get_db
from app.core.security import get_api_key, mask_token
from app.modules.plex.models import PlexUser
from app.modules.plex.service import (
    get_watchlistAllUsers, 
    remove_from_all_user_watchlists, 
    get_watchlist_items_not_in_plexLibrary,
)
from app.modules.plex.schemas import (
    PlexUserCreate,
    PlexUserUpdate,
    PlexUserResponse,
    PlexItemData,
)

logger = logging.getLogger(__name__)

from app.modules.plex.constants import MODULE_PREFIX, USERS_PREFIX, WISHLIST_PREFIX, SYNC_PREFIX

# Main router that combines all sub-routers
router = APIRouter(tags=[MODULE_PREFIX.strip("/")])

# Sub-routers
users_router = APIRouter(prefix=USERS_PREFIX, tags=["users"])
wishlist_router = APIRouter(prefix=WISHLIST_PREFIX, tags=["wishlist"])



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

@wishlist_router.get("", response_model=List[PlexItemData])
async def get_wishlist(
    search: Optional[str] = Query(None, description="Search term for title"),
    year: Optional[int] = Query(None, description="Filter by year"),
    media_type: Optional[str] = Query(None, description="Filter by media type (movie, show)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: Session = Depends(get_db),
):
    try:
        return await get_watchlistAllUsers(db)
    except Exception as e:
        logger.error(f"Error getting wishlist: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get wishlist: {str(e)}"
        )



@wishlist_router.delete("/delete-all", status_code=status.HTTP_200_OK)
async def delete_all_wishlist_items(
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key),
    confirm: bool = Query(False, description="Must be True to confirm deletion"),
):
    """
    Delete all wishlist items from the users watchlists.
    
    WARNING: This permanently deletes all wishlist items from the users watchlists.
    It does NOT remove them from Plex watchlists - it only removes them from local storage.
    
    Requires confirmation via query parameter: ?confirm=true
    """
    try:
        return await remove_from_all_user_watchlists(db)
    except Exception as e:
        logger.error(f"Error deleting all wishlist items: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete all wishlist items: {str(e)}"
        )


@wishlist_router.post("", response_model=List[PlexItemData])
async def get_watchlist_items_not_in_plexLibrary_route(
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key),
):
    """Get all watchlist items that are not in the plexLibrary."""
    try:
        return await get_watchlist_items_not_in_plexLibrary(db,remove_from_watchlist=True)
    except Exception as e:
        logger.error(f"Error getting watchlist items not in plexLibrary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get watchlist items not in plexLibrary: {str(e)}",
        )


# ============================================================================
# INCLUDE SUB-ROUTERS
# ============================================================================

router.include_router(users_router)
router.include_router(wishlist_router)

