from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.factories.plex.plexUsersFactory import (
    createGetPlexUserQuery,
    createGetPlexUserByIdQuery,
    createGetPlexUserByNameQuery,
    createGetPlexUserByPlexTokenQuery,
    createCreatePlexUserUseCase,
    createUpdatePlexUserUseCase,
    createDeletePlexUserUseCase,
)
from app.application.plex.queries.getPlexUsers import (
    GetPlexUserQuery,
    GetPlexUserByIdQuery,
    GetPlexUserByNameQuery,
    GetPlexUserByPlexTokenQuery,
)
from app.application.plex.useCases.createPlexUser import CreatePlexUserUseCase
from app.application.plex.useCases.updatePlexUser import UpdatePlexUserUseCase
from app.application.plex.useCases.deletePlexUser import DeletePlexUserUseCase
from app.adapters.http.schemas.plex.plexUserSchema import (
    CreatePlexUserRequest,
    CreatePlexUserResponse,
    UpdatePlexUserRequest,
)
from app.domain.models.plexUser import PlexUser

plexUserRoutes = APIRouter(prefix="/users", tags=["plex-users"])


@plexUserRoutes.get("/", response_model=List[PlexUser])
async def get_plex_users(query: GetPlexUserQuery = Depends(createGetPlexUserQuery)):
    """Get all active Plex users."""
    users = await query.execute()
    return users


@plexUserRoutes.get("/{user_id}", response_model=PlexUser)
async def get_plex_user_by_id(
    user_id: int, query: GetPlexUserByIdQuery = Depends(createGetPlexUserByIdQuery)
):
    """Get a Plex user by ID."""
    user = await query.execute(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Plex user not found")
    return user


@plexUserRoutes.get("/name/{name}", response_model=PlexUser)
async def get_plex_user_by_name(
    name: str, query: GetPlexUserByNameQuery = Depends(createGetPlexUserByNameQuery)
):
    """Get a Plex user by name."""
    user = await query.execute(name)
    if not user:
        raise HTTPException(status_code=404, detail="Plex user not found")
    return user


@plexUserRoutes.post("/", response_model=CreatePlexUserResponse)
async def create_plex_user(
    request: CreatePlexUserRequest,
    use_case: CreatePlexUserUseCase = Depends(createCreatePlexUserUseCase),
):
    """Create a new Plex user."""
    user = PlexUser(
        name=request.name,
        plex_token=request.plex_token,
        active=True,
    )
    created_user = await use_case.execute(user)
    return CreatePlexUserResponse(
        name=created_user.name,
        plex_token=created_user.plex_token,
        active=created_user.active,
        created_at=created_user.created_at,
        updated_at=created_user.updated_at,
        token_masked=created_user.plex_token[:4] + "***" if created_user.plex_token else "***",
    )


@plexUserRoutes.put("/{user_id}", response_model=PlexUser)
async def update_plex_user(
    user_id: int,
    request: UpdatePlexUserRequest,
    use_case: UpdatePlexUserUseCase = Depends(createUpdatePlexUserUseCase),
    query: GetPlexUserByIdQuery = Depends(createGetPlexUserByIdQuery),
):
    """Update a Plex user."""
    existing_user = await query.execute(user_id)
    if not existing_user:
        raise HTTPException(status_code=404, detail="Plex user not found")
    
    # Update only provided fields
    updated_user = PlexUser(
        id=user_id,
        name=request.name if request.name is not None else existing_user.name,
        plex_token=request.plex_token if request.plex_token is not None else existing_user.plex_token,
        active=request.active if request.active is not None else existing_user.active,
        created_at=existing_user.created_at,
        updated_at=existing_user.updated_at,
    )
    result = await use_case.execute(updated_user)
    if not result:
        raise HTTPException(status_code=404, detail="Plex user not found")
    return result


@plexUserRoutes.delete("/{user_id}", response_model=PlexUser)
async def delete_plex_user(
    user_id: int,
    use_case: DeletePlexUserUseCase = Depends(createDeletePlexUserUseCase),
    query: GetPlexUserByIdQuery = Depends(createGetPlexUserByIdQuery),
):
    """Delete a Plex user."""
    existing_user = await query.execute(user_id)
    if not existing_user:
        raise HTTPException(status_code=404, detail="Plex user not found")
    
    result = await use_case.execute(existing_user)
    if not result:
        raise HTTPException(status_code=404, detail="Plex user not found")
    return result

