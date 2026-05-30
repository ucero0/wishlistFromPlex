"""Verify PLEX_SERVER_ADMIN_TOKEN against the local Plex Media Server."""
from app.domain.errors.external import ExternalServiceError
from app.domain.models.external_connection import ExternalConnectionStatus
from app.domain.ports.external.plex.plex_server_library_provider import (
    PlexServerLibraryProvider,
)
from app.domain.services.connection_probe import (
    connection_status_from_error,
    connection_status_ok,
)


class TestPlexServerAdminTokenQuery:
    def __init__(self, provider: PlexServerLibraryProvider):
        self._provider = provider

    async def execute(self) -> ExternalConnectionStatus:
        try:
            await self._provider.get_library_locations_by_media()
            return connection_status_ok("plex")
        except ExternalServiceError as exc:
            return connection_status_from_error(exc)
