"""Adapter for Prowlarr - bridges infrastructure and domain."""
import logging
from typing import List

from app.adapters.external.prowlarr.mapper import to_domain_list
from app.domain.errors.external import ExternalServiceError
from app.domain.models.external_connection import ExternalConnectionStatus
from app.domain.models.prowlarr_indexer import ProwlarrIndexerInfo
from app.domain.models.torrent_search import TorrentSearchResult
from app.domain.ports.external.prowlarr.torrent_search_provider import TorrentSearchProvider
from app.domain.services.connection_probe import (
    connection_status_from_error,
    connection_status_ok,
)
from app.infrastructure.external_apis.prowlarr.prowlarr_client import ProwlarrClient

logger = logging.getLogger(__name__)


class ProwlarrAdapter(TorrentSearchProvider):
    """Adapter that converts Prowlarr infrastructure to domain models."""

    def __init__(self, client: ProwlarrClient):
        self.client = client

    async def search_torrents(
        self,
        query: str,
        media_type: str = "movie",
    ) -> List[TorrentSearchResult]:
        categories = "2000" if media_type == "movie" else "5000"
        logger.info("Searching Prowlarr: '%s', media_type: %s", query, media_type)
        raw_results = await self.client.search(query, categories)
        return to_domain_list(raw_results)

    async def send_to_download_client(self, guid: str, indexer_id: int) -> bool:
        return await self.client.send_to_download_client(guid, indexer_id)

    async def test_connection(self) -> ExternalConnectionStatus:
        try:
            version = await self.client.probe_connection()
            return connection_status_ok("prowlarr", version=version or None)
        except ExternalServiceError as exc:
            return connection_status_from_error(exc)
        except Exception as exc:
            logger.exception("Unexpected error testing Prowlarr connection")
            return ExternalConnectionStatus(
                service="prowlarr",
                connected=False,
                error=str(exc),
                error_type="connection",
            )

    async def get_indexers(self) -> List[ProwlarrIndexerInfo]:
        raw_indexers = await self.client.get_indexers()
        return [
            ProwlarrIndexerInfo(
                id=indexer.id,
                name=indexer.name,
                enabled=indexer.enable,
            )
            for indexer in raw_indexers
        ]
