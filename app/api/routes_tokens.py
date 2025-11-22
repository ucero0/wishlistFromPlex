from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.db import get_db
from app.core.security import get_api_key, mask_token
from app.models.plex_user import PlexUser
from app.api.schemas import PlexUserCreate, PlexUserUpdate, PlexUserResponse

router = APIRouter(prefix="/api/users", tags=["users"])


@router.post("", response_model=PlexUserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: PlexUserCreate,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key),
):
    """Create a new Plex user entry."""
    # Check if name already exists
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


@router.get("", response_model=List[PlexUserResponse])
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


@router.get("/{user_id}", response_model=PlexUserResponse)
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


@router.patch("/{user_id}", response_model=PlexUserResponse)
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
        # Check if new name conflicts with existing user
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


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
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



