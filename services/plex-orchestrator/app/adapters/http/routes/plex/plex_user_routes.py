from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.factories.plex.plex_users_factory import (
    create_get_plex_user_query,
    create_get_plex_user_by_id_query,
    create_get_plex_user_by_name_query,
    create_get_plex_user_by_plex_token_query,
    create_create_plex_user_use_case,
    create_update_plex_user_use_case,
    create_delete_plex_user_use_case,
)
from app.application.plex.queries.get_plex_users_query import (
    GetPlexUserQuery,
    GetPlexUserByIdQuery,
    GetPlexUserByNameQuery,
    GetPlexUserByPlexTokenQuery,
)
from app.application.plex.use_cases.create_plex_user_use_case import CreatePlexUserUseCase
from app.application.plex.use_cases.update_plex_user_use_case import UpdatePlexUserUseCase
from app.application.plex.use_cases.delete_plex_user_use_case import DeletePlexUserUseCase
from app.adapters.http.schemas.plex.plex_user_schemas import (
    CreatePlexUserRequest,
    CreatePlexUserResponse,
    UpdatePlexUserRequest,
)
from app.domain.models.plex_user import PlexUser

plex_user_routes = APIRouter(prefix="/users", tags=["plex-users"])


@plex_user_routes.get("/", response_model=List[PlexUser])
async def get_plex_users(query: GetPlexUserQuery = Depends(create_get_plex_user_query)):
    """Get all active Plex users."""
    users = await query.execute()
    return users


@plex_user_routes.get("/{user_id}", response_model=PlexUser)
async def get_plex_user_by_id(
    user_id: int, query: GetPlexUserByIdQuery = Depends(create_get_plex_user_by_id_query)
):
    """Get a Plex user by ID."""
    user = await query.execute(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Plex user not found")
    return user


@plex_user_routes.get("/name/{name}", response_model=PlexUser)
async def get_plex_user_by_name(
    name: str, query: GetPlexUserByNameQuery = Depends(create_get_plex_user_by_name_query)
):
    """Get a Plex user by name."""
    user = await query.execute(name)
    if not user:
        raise HTTPException(status_code=404, detail="Plex user not found")
    return user


@plex_user_routes.post("/", response_model=CreatePlexUserResponse)
async def create_plex_user(
    request: CreatePlexUserRequest,
    use_case: CreatePlexUserUseCase = Depends(create_create_plex_user_use_case),
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


@plex_user_routes.put("/{user_id}", response_model=PlexUser)
async def update_plex_user(
    user_id: int,
    request: UpdatePlexUserRequest,
    use_case: UpdatePlexUserUseCase = Depends(create_update_plex_user_use_case),
    query: GetPlexUserByIdQuery = Depends(create_get_plex_user_by_id_query),
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


@plex_user_routes.delete("/{user_id}", response_model=PlexUser)
async def delete_plex_user(
    user_id: int,
    use_case: DeletePlexUserUseCase = Depends(create_delete_plex_user_use_case),
    query: GetPlexUserByIdQuery = Depends(create_get_plex_user_by_id_query),
):
    """Delete a Plex user."""
    existing_user = await query.execute(user_id)
    if not existing_user:
        raise HTTPException(status_code=404, detail="Plex user not found")
    
    result = await use_case.execute(existing_user)
    if not result:
        raise HTTPException(status_code=404, detail="Plex user not found")
    return result

