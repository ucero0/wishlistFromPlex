"""Factory for Plex user related use cases."""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.plex.queries.get_plex_users_query import (
    GetPlexUserByIdQuery,
    GetPlexUserByNameQuery,
    GetPlexUserByPlexTokenQuery,
    GetPlexUserQuery,
)
from app.application.plex.use_cases.create_plex_user_use_case import CreatePlexUserUseCase
from app.application.plex.use_cases.delete_plex_user_use_case import DeletePlexUserUseCase
from app.application.plex.use_cases.update_plex_user_use_case import UpdatePlexUserUseCase
from app.composition.plex_users import (
    build_create_plex_user_use_case,
    build_delete_plex_user_use_case,
    build_get_plex_user_by_id_query,
    build_get_plex_user_by_name_query,
    build_get_plex_user_by_plex_token_query,
    build_get_plex_user_query,
    build_update_plex_user_use_case,
)
from app.infrastructure.persistence.database import get_db


def create_get_plex_user_query(
    session: AsyncSession = Depends(get_db),
) -> GetPlexUserQuery:
    return build_get_plex_user_query(session)


def create_get_plex_user_by_id_query(
    session: AsyncSession = Depends(get_db),
) -> GetPlexUserByIdQuery:
    return build_get_plex_user_by_id_query(session)


def create_get_plex_user_by_name_query(
    session: AsyncSession = Depends(get_db),
) -> GetPlexUserByNameQuery:
    return build_get_plex_user_by_name_query(session)


def create_get_plex_user_by_plex_token_query(
    session: AsyncSession = Depends(get_db),
) -> GetPlexUserByPlexTokenQuery:
    return build_get_plex_user_by_plex_token_query(session)


def create_create_plex_user_use_case(
    session: AsyncSession = Depends(get_db),
) -> CreatePlexUserUseCase:
    return build_create_plex_user_use_case(session)


def create_update_plex_user_use_case(
    session: AsyncSession = Depends(get_db),
) -> UpdatePlexUserUseCase:
    return build_update_plex_user_use_case(session)


def create_delete_plex_user_use_case(
    session: AsyncSession = Depends(get_db),
) -> DeletePlexUserUseCase:
    return build_delete_plex_user_use_case(session)
