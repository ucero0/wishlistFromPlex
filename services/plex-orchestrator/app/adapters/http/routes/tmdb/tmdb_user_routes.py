from fastapi import APIRouter, Depends, HTTPException
from typing import List

from app.adapters.http.schemas.tmdb.tmdb_user_schemas import (
    CreateTmdbUserRequest,
    CreateTmdbUserResponse,
    UpdateTmdbUserRequest,
)
from app.application.tmdb.queries.get_tmdb_users_query import (
    GetTmdbUserByIdQuery,
    GetTmdbUserByNameQuery,
    GetTmdbUserQuery,
)
from app.application.tmdb.use_cases.create_tmdb_user_use_case import CreateTmdbUserUseCase
from app.application.tmdb.use_cases.delete_tmdb_user_use_case import DeleteTmdbUserUseCase
from app.application.tmdb.use_cases.update_tmdb_user_use_case import UpdateTmdbUserUseCase
from app.domain.models.tmdb_user import TmdbUser
from app.factories.tmdb.tmdb_users_factory import (
    create_create_tmdb_user_use_case,
    create_delete_tmdb_user_use_case,
    create_get_tmdb_user_by_id_query,
    create_get_tmdb_user_by_name_query,
    create_get_tmdb_user_query,
    create_update_tmdb_user_use_case,
)

tmdb_user_routes = APIRouter(prefix="/users", tags=["tmdb-users"])


@tmdb_user_routes.get("/", response_model=List[TmdbUser])
async def get_tmdb_users(query: GetTmdbUserQuery = Depends(create_get_tmdb_user_query)):
    return await query.execute()


@tmdb_user_routes.get("/{user_id}", response_model=TmdbUser)
async def get_tmdb_user_by_id(
    user_id: int, query: GetTmdbUserByIdQuery = Depends(create_get_tmdb_user_by_id_query)
):
    user = await query.execute(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="TMDB user not found")
    return user


@tmdb_user_routes.get("/name/{name}", response_model=TmdbUser)
async def get_tmdb_user_by_name(
    name: str, query: GetTmdbUserByNameQuery = Depends(create_get_tmdb_user_by_name_query)
):
    user = await query.execute(name)
    if not user:
        raise HTTPException(status_code=404, detail="TMDB user not found")
    return user


@tmdb_user_routes.post("/", response_model=CreateTmdbUserResponse)
async def create_tmdb_user(
    request: CreateTmdbUserRequest,
    use_case: CreateTmdbUserUseCase = Depends(create_create_tmdb_user_use_case),
):
    user = TmdbUser(
        name=request.name,
        access_token=request.access_token,
        account_id=request.account_id,
        active=True,
    )
    created = await use_case.execute(user)
    return CreateTmdbUserResponse(
        name=created.name,
        account_id=created.account_id or 0,
        active=created.active,
        created_at=created.created_at,
        updated_at=created.updated_at,
        token_masked=created.access_token[:4] + "***"
        if created.access_token
        else "***",
    )


@tmdb_user_routes.put("/{user_id}", response_model=TmdbUser)
async def update_tmdb_user(
    user_id: int,
    request: UpdateTmdbUserRequest,
    use_case: UpdateTmdbUserUseCase = Depends(create_update_tmdb_user_use_case),
    query: GetTmdbUserByIdQuery = Depends(create_get_tmdb_user_by_id_query),
):
    existing = await query.execute(user_id)
    if not existing:
        raise HTTPException(status_code=404, detail="TMDB user not found")
    updated = TmdbUser(
        id=user_id,
        name=request.name if request.name is not None else existing.name,
        access_token=request.access_token
        if request.access_token is not None
        else existing.access_token,
        account_id=request.account_id
        if request.account_id is not None
        else existing.account_id,
        active=request.active if request.active is not None else existing.active,
        created_at=existing.created_at,
        updated_at=existing.updated_at,
    )
    result = await use_case.execute(updated)
    if not result:
        raise HTTPException(status_code=404, detail="TMDB user not found")
    return result


@tmdb_user_routes.delete("/{user_id}", response_model=TmdbUser)
async def delete_tmdb_user(
    user_id: int,
    use_case: DeleteTmdbUserUseCase = Depends(create_delete_tmdb_user_use_case),
    query: GetTmdbUserByIdQuery = Depends(create_get_tmdb_user_by_id_query),
):
    existing = await query.execute(user_id)
    if not existing:
        raise HTTPException(status_code=404, detail="TMDB user not found")
    result = await use_case.execute(existing)
    if not result:
        raise HTTPException(status_code=404, detail="TMDB user not found")
    return result
