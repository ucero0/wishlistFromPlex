"""Resolve Plex server admin token: database override, then environment."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Optional

from app.core.config import settings
from app.domain.errors.plex import PlexServerAdminTokenNotConfiguredError
from app.infrastructure.persistence.database import async_session_scope
from app.infrastructure.persistence.plex.repo.plex_server_config_repository import (
    PlexServerConfigRepository,
)

PlexServerAdminTokenSource = Literal["database", "environment", "none"]


@dataclass(frozen=True)
class PlexServerAdminTokenStatus:
    configured: bool
    source: PlexServerAdminTokenSource
    token_masked: Optional[str]
    updated_at: Optional[datetime]


def mask_plex_token(token: str | None) -> Optional[str]:
    if not token:
        return None
    stripped = token.strip()
    if len(stripped) >= 4:
        return stripped[:4] + "***"
    return "***"


class PlexServerAdminTokenResolver:
    async def resolve(self) -> str:
        db_token = await self._get_database_token()
        if db_token:
            return db_token
        env_token = self._get_environment_token()
        if env_token:
            return env_token
        raise PlexServerAdminTokenNotConfiguredError(
            "Plex server admin token is not configured. "
            "Set PLEX_SERVER_ADMIN_TOKEN in .env or POST /plex/servers/admin-token."
        )

    async def get_status(self) -> PlexServerAdminTokenStatus:
        db_config = await self._get_database_config()
        if db_config and db_config.admin_token.strip():
            return PlexServerAdminTokenStatus(
                configured=True,
                source="database",
                token_masked=mask_plex_token(db_config.admin_token),
                updated_at=db_config.updated_at,
            )
        env_token = self._get_environment_token()
        if env_token:
            return PlexServerAdminTokenStatus(
                configured=True,
                source="environment",
                token_masked=mask_plex_token(env_token),
                updated_at=None,
            )
        return PlexServerAdminTokenStatus(
            configured=False,
            source="none",
            token_masked=None,
            updated_at=None,
        )

    async def _get_database_config(self):
        async with async_session_scope() as session:
            return await PlexServerConfigRepository(session).get_config()

    async def _get_database_token(self) -> Optional[str]:
        config = await self._get_database_config()
        if config and config.admin_token.strip():
            return config.admin_token.strip()
        return None

    def _get_environment_token(self) -> Optional[str]:
        token = settings.plex_server_admin_token
        if token is None or not str(token).strip():
            return None
        return str(token).strip()


plex_server_admin_token_resolver = PlexServerAdminTokenResolver()
