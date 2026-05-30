"""Factory for Plex server admin token endpoints."""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.plex.queries.get_plex_server_admin_token_config_query import (
    GetPlexServerAdminTokenConfigQuery,
)
from app.application.plex.use_cases.upsert_plex_server_admin_token_use_case import (
    UpsertPlexServerAdminTokenUseCase,
)
from app.composition.plex_server_config import (
    build_get_plex_server_admin_token_config_query,
    build_upsert_plex_server_admin_token_use_case,
)
from app.infrastructure.persistence.database import get_db


def create_get_plex_server_admin_token_config_query() -> GetPlexServerAdminTokenConfigQuery:
    return build_get_plex_server_admin_token_config_query()


def create_upsert_plex_server_admin_token_use_case(
    session: AsyncSession = Depends(get_db),
) -> UpsertPlexServerAdminTokenUseCase:
    return build_upsert_plex_server_admin_token_use_case(session)
