"""Query: current Plex server admin token configuration."""
from app.application.plex.services.plex_server_admin_token_resolver import (
    PlexServerAdminTokenResolver,
    PlexServerAdminTokenStatus,
)


class GetPlexServerAdminTokenConfigQuery:
    def __init__(self, token_resolver: PlexServerAdminTokenResolver):
        self._token_resolver = token_resolver

    async def execute(self) -> PlexServerAdminTokenStatus:
        return await self._token_resolver.get_status()
