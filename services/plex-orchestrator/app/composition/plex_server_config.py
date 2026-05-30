"""Composition root for Plex server admin token config."""
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.plex.queries.get_plex_server_admin_token_config_query import (
    GetPlexServerAdminTokenConfigQuery,
)
from app.application.plex.services.plex_server_admin_token_resolver import (
    plex_server_admin_token_resolver,
)
from app.application.plex.use_cases.upsert_plex_server_admin_token_use_case import (
    UpsertPlexServerAdminTokenUseCase,
)
from app.composition.persistence import build_plex_server_config_repository
from app.infrastructure.external_apis.plex.plex_server.client import (
    PlexServerLibraryApiClient,
)


def build_get_plex_server_admin_token_config_query() -> GetPlexServerAdminTokenConfigQuery:
    return GetPlexServerAdminTokenConfigQuery(plex_server_admin_token_resolver)


def build_upsert_plex_server_admin_token_use_case(
    session: AsyncSession,
) -> UpsertPlexServerAdminTokenUseCase:
    return UpsertPlexServerAdminTokenUseCase(
        build_plex_server_config_repository(session),
        PlexServerLibraryApiClient(plex_server_admin_token_resolver),
    )
