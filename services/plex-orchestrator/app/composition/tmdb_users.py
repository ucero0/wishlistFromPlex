"""Composition root for TMDB user queries and use cases."""
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.tmdb.queries.get_tmdb_users_query import (
    GetTmdbUserByIdQuery,
    GetTmdbUserByNameQuery,
    GetTmdbUserQuery,
)
from app.application.tmdb.use_cases.create_tmdb_user_use_case import CreateTmdbUserUseCase
from app.application.tmdb.use_cases.delete_tmdb_user_use_case import DeleteTmdbUserUseCase
from app.application.tmdb.use_cases.ensure_tmdb_user_from_env_use_case import (
    EnsureTmdbUserFromEnvUseCase,
)
from app.application.tmdb.use_cases.update_tmdb_user_use_case import UpdateTmdbUserUseCase
from app.composition.persistence import build_tmdb_user_repository
from app.composition.tmdb import build_tmdb_watchlist_adapter


def build_get_tmdb_user_query(session: AsyncSession) -> GetTmdbUserQuery:
    return GetTmdbUserQuery(build_tmdb_user_repository(session))


def build_get_tmdb_user_by_id_query(session: AsyncSession) -> GetTmdbUserByIdQuery:
    return GetTmdbUserByIdQuery(build_tmdb_user_repository(session))


def build_get_tmdb_user_by_name_query(session: AsyncSession) -> GetTmdbUserByNameQuery:
    return GetTmdbUserByNameQuery(build_tmdb_user_repository(session))


def build_create_tmdb_user_use_case(session: AsyncSession) -> CreateTmdbUserUseCase:
    return CreateTmdbUserUseCase(
        build_tmdb_user_repository(session),
        build_tmdb_watchlist_adapter(),
    )


def build_update_tmdb_user_use_case(session: AsyncSession) -> UpdateTmdbUserUseCase:
    return UpdateTmdbUserUseCase(
        build_tmdb_user_repository(session),
        build_tmdb_watchlist_adapter(),
    )


def build_delete_tmdb_user_use_case(session: AsyncSession) -> DeleteTmdbUserUseCase:
    return DeleteTmdbUserUseCase(build_tmdb_user_repository(session))


def build_ensure_tmdb_user_from_env_use_case(
    session: AsyncSession,
) -> EnsureTmdbUserFromEnvUseCase:
    return EnsureTmdbUserFromEnvUseCase(
        build_tmdb_user_repository(session),
        build_create_tmdb_user_use_case(session),
    )
