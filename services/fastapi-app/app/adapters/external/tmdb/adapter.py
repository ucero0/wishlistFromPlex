"""Adapter for TMDB - bridges infrastructure and domain."""
import logging
from typing import Optional, Tuple

from app.domain.errors.tmdb import TMDBConfigurationError, TMDBError
from app.domain.models.external_connection import ExternalConnectionStatus
from app.domain.ports.external.tmdb.tmdbProvider import TMDBProvider
from app.infrastructure.externalApis.tmdb.client import TMDBClient

logger = logging.getLogger(__name__)


class TMDBAdapter(TMDBProvider):
    """Adapter that converts TMDB infrastructure to domain models."""

    def __init__(self, client: TMDBClient):
        self.client = client

    async def test_connection(self) -> ExternalConnectionStatus:
        try:
            connected = await self.client.test_connection()
            if connected:
                return ExternalConnectionStatus(service="tmdb", connected=True)
            api_key = getattr(self.client, "api_key", None)
            if not api_key or not str(api_key).strip():
                return ExternalConnectionStatus(
                    service="tmdb",
                    connected=False,
                    error="TMDB API key is not configured",
                )
            return ExternalConnectionStatus(
                service="tmdb",
                connected=False,
                error="Cannot connect to TMDB API",
            )
        except TMDBError as exc:
            return ExternalConnectionStatus(
                service="tmdb", connected=False, error=exc.message
            )
        except Exception as exc:
            logger.exception("Unexpected error testing TMDB connection")
            return ExternalConnectionStatus(
                service="tmdb", connected=False, error=str(exc)
            )

    async def get_original_title_and_language(
        self,
        title: str,
        year: int,
        media_type: str,
    ) -> Optional[Tuple[str, str]]:
        try:
            logger.info("Searching TMDB for %s: %s (%s)", media_type, title, year)
            response = await self.client.search(
                title=title,
                year=year,
                media_type=media_type,
            )
            if not response:
                return None
            if media_type == "movie":
                return (response.original_title, response.original_language)
            return (response.original_name, response.original_language)
        except TMDBConfigurationError:
            logger.warning(
                "TMDB API key is not configured, skipping search for %s (%s)",
                title,
                year,
            )
            return None
