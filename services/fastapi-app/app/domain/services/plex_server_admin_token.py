"""Backward-compatible helper; prefer PlexServerAdminTokenResolver."""
from app.application.plex.services.plex_server_admin_token_resolver import (
    PlexServerAdminTokenResolver,
    plex_server_admin_token_resolver,
)

_resolver = plex_server_admin_token_resolver


async def require_plex_server_admin_token() -> str:
    return await _resolver.resolve()
