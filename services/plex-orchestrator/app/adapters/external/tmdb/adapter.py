"""Adapter for TMDB - bridges infrastructure and domain."""
import logging
from typing import Optional, Tuple

from app.domain.errors.tmdb import TMDBConfigurationError
from app.domain.models.external_connection import ExternalConnectionStatus
from app.domain.ports.external.tmdb.tmdb_provider import TMDBProvider
from app.domain.services.connection_probe import capture_async_connection_probe
from app.infrastructure.external_apis.tmdb.client import TMDBClient

logger = logging.getLogger(__name__)


class TMDBAdapter(TMDBProvider):
    """Adapter that converts TMDB infrastructure to domain models."""

    def __init__(self, client: TMDBClient):
        self.client = client

    async def test_connection(self) -> ExternalConnectionStatus:
        return await capture_async_connection_probe(
            "tmdb",
            self.client.probe_connection,
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
