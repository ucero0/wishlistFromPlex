"""Create or update the Plex server admin token in the database."""
from app.application.plex.services.plex_server_admin_token_resolver import mask_plex_token
from app.domain.models.plex_server_config import PlexServerConfig
from app.domain.ports.repositories.plex.plex_server_config_repository_port import (
    PlexServerConfigRepositoryPort,
)
from app.infrastructure.external_apis.plex.plex_server.client import (
    PlexServerLibraryApiClient,
)


class UpsertPlexServerAdminTokenUseCase:
    def __init__(
        self,
        repo: PlexServerConfigRepositoryPort,
        plex_server_client: PlexServerLibraryApiClient,
    ):
        self._repo = repo
        self._client = plex_server_client

    async def execute(self, admin_token: str) -> tuple[PlexServerConfig, str, bool]:
        """
        Validate token against Plex, then persist to DB.

        Returns (config, token_masked, created) where created is True on first insert.
        """
        token = admin_token.strip()
        if not token:
            raise ValueError("admin_token must not be empty")

        await self._client.validate_admin_token(token)

        existing = await self._repo.get_config()
        created = existing is None
        config = await self._repo.upsert_admin_token(token)
        return config, mask_plex_token(token) or "***", created
