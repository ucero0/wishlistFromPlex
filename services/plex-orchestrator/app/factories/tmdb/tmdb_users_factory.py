"""Factory for TMDB user related use cases."""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.tmdb.queries.get_tmdb_users_query import (
    GetTmdbUserByIdQuery,
    GetTmdbUserByNameQuery,
    GetTmdbUserQuery,
)
from app.application.tmdb.use_cases.create_tmdb_user_use_case import CreateTmdbUserUseCase
from app.application.tmdb.use_cases.delete_tmdb_user_use_case import DeleteTmdbUserUseCase
from app.application.tmdb.use_cases.update_tmdb_user_use_case import UpdateTmdbUserUseCase
from app.composition.tmdb_users import (
    build_create_tmdb_user_use_case,
    build_delete_tmdb_user_use_case,
    build_get_tmdb_user_by_id_query,
    build_get_tmdb_user_by_name_query,
    build_get_tmdb_user_query,
    build_update_tmdb_user_use_case,
)
from app.infrastructure.persistence.database import get_db


def create_get_tmdb_user_query(
    session: AsyncSession = Depends(get_db),
) -> GetTmdbUserQuery:
    return build_get_tmdb_user_query(session)


def create_get_tmdb_user_by_id_query(
    session: AsyncSession = Depends(get_db),
) -> GetTmdbUserByIdQuery:
    return build_get_tmdb_user_by_id_query(session)


def create_get_tmdb_user_by_name_query(
    session: AsyncSession = Depends(get_db),
) -> GetTmdbUserByNameQuery:
    return build_get_tmdb_user_by_name_query(session)


def create_create_tmdb_user_use_case(
    session: AsyncSession = Depends(get_db),
) -> CreateTmdbUserUseCase:
    return build_create_tmdb_user_use_case(session)


def create_update_tmdb_user_use_case(
    session: AsyncSession = Depends(get_db),
) -> UpdateTmdbUserUseCase:
    return build_update_tmdb_user_use_case(session)


def create_delete_tmdb_user_use_case(
    session: AsyncSession = Depends(get_db),
) -> DeleteTmdbUserUseCase:
    return build_delete_tmdb_user_use_case(session)
