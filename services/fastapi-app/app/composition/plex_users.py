"""Composition root for Plex user queries and use cases."""
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
from app.composition.plex_external import build_get_watchlist_query
from app.composition.persistence import build_plex_user_repository


def build_get_plex_user_query(session: AsyncSession) -> GetPlexUserQuery:
    return GetPlexUserQuery(build_plex_user_repository(session))


def build_get_plex_user_by_id_query(session: AsyncSession) -> GetPlexUserByIdQuery:
    return GetPlexUserByIdQuery(build_plex_user_repository(session))


def build_get_plex_user_by_name_query(session: AsyncSession) -> GetPlexUserByNameQuery:
    return GetPlexUserByNameQuery(build_plex_user_repository(session))


def build_get_plex_user_by_plex_token_query(
    session: AsyncSession,
) -> GetPlexUserByPlexTokenQuery:
    return GetPlexUserByPlexTokenQuery(build_plex_user_repository(session))


def build_create_plex_user_use_case(session: AsyncSession) -> CreatePlexUserUseCase:
    return CreatePlexUserUseCase(
        build_plex_user_repository(session),
        build_get_watchlist_query(),
    )


def build_update_plex_user_use_case(session: AsyncSession) -> UpdatePlexUserUseCase:
    return UpdatePlexUserUseCase(
        build_plex_user_repository(session),
        build_get_watchlist_query(),
    )


def build_delete_plex_user_use_case(session: AsyncSession) -> DeletePlexUserUseCase:
    return DeletePlexUserUseCase(build_plex_user_repository(session))
