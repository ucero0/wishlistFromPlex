"""Prowlarr API client."""
import asyncio
import logging
from typing import List, Optional, Tuple

import httpx

from app.core.config import settings
from app.domain.errors.prowlarr import (
    ProwlarrConnectionError,
    ProwlarrDownloadError,
    ProwlarrOperationError,
)
from app.infrastructure.external_apis.prowlarr.schemas import (
    ProwlarrIndexer,
    ProwlarrRawResult,
)
from app.infrastructure.http_errors import raise_mapped_httpx_error

logger = logging.getLogger(__name__)


def is_deluge_torrent_already_in_session(response_body: str) -> bool:
    """True when Prowlarr/Deluge reject a duplicate add (HTTP 500, torrent already present)."""
    lower = response_body.lower()
    return "torrent already in session" in lower or "addtorrenterror" in lower


class ProwlarrClient:
    """Client for interacting with Prowlarr API."""

    def __init__(self):
        self.base_url = f"http://{settings.prowlarr_host}:{settings.prowlarr_port}"
        self.headers = {
            "Content-Type": "application/json",
            "X-Api-Key": settings.prowlarr_api_key,
        }

    def _target(self) -> str:
        return self.base_url

    async def probe_connection(self) -> str:
        """Raise when Prowlarr is unreachable; return version on success."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/system/status",
                    headers=self.headers,
                )
                response.raise_for_status()
                data = response.json()
                version = data.get("version")
                return str(version) if version is not None else ""
        except Exception as exc:
            raise_mapped_httpx_error(
                exc,
                connection_error_type=ProwlarrConnectionError,
                operation_error_type=ProwlarrOperationError,
                target=self._target(),
                operation="connection probe",
            )

    async def get_indexers(self) -> List[ProwlarrIndexer]:
        """Get all indexers from Prowlarr."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/indexer",
                    headers=self.headers,
                )
                response.raise_for_status()
                indexers_data = response.json()
                return [ProwlarrIndexer(**indexer) for indexer in indexers_data]
        except Exception as exc:
            logger.error("Error getting Prowlarr indexers: %s", exc)
            raise_mapped_httpx_error(
                exc,
                connection_error_type=ProwlarrConnectionError,
                operation_error_type=ProwlarrOperationError,
                target=self._target(),
                operation="list indexers",
            )

    async def search(self, query: str, categories: str = "2000") -> List[ProwlarrRawResult]:
        """Search Prowlarr for torrents. Empty list means no matches, not a failure."""
        try:
            timeout = httpx.Timeout(120.0, connect=10.0)
            async with httpx.AsyncClient(timeout=timeout) as client:
                logger.info(
                    "Searching Prowlarr for: '%s' (categories: %s)", query, categories
                )
                response = await client.get(
                    f"{self.base_url}/api/v1/search",
                    headers=self.headers,
                    params={
                        "query": query,
                        "categories": categories,
                        "type": "search",
                    },
                )
                response.raise_for_status()
                api_response_data = response.json()

                if not isinstance(api_response_data, list):
                    raise ProwlarrOperationError(
                        f"Unexpected Prowlarr search response format: {type(api_response_data)}"
                    )

                results: List[ProwlarrRawResult] = []
                for item in api_response_data:
                    try:
                        results.append(ProwlarrRawResult(**item))
                    except Exception as parse_exc:
                        logger.warning(
                            "Failed to parse Prowlarr result: %s", parse_exc
                        )
                logger.info(
                    "Prowlarr search returned %s result(s) for query: '%s'",
                    len(results),
                    query,
                )
                return results
        except asyncio.CancelledError:
            logger.warning("Prowlarr search cancelled for query '%s'", query)
            raise
        except Exception as exc:
            logger.error("Prowlarr search failed for query '%s': %s", query, exc)
            raise_mapped_httpx_error(
                exc,
                connection_error_type=ProwlarrConnectionError,
                operation_error_type=ProwlarrOperationError,
                target=self._target(),
                operation="search torrents",
            )

    async def send_to_download_client(self, guid: str, indexer_id: int) -> bool:
        """Send torrent to download client via Prowlarr."""
        try:
            # Grab can re-fetch from indexer (FlareSolverr) and push to Deluge — allow same budget as search.
            timeout = httpx.Timeout(120.0, connect=10.0)
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/search",
                    headers=self.headers,
                    json={"guid": guid, "indexerId": indexer_id},
                )
                if response.status_code == 200:
                    return True
                body = response.text
                if is_deluge_torrent_already_in_session(body):
                    logger.info(
                        "Torrent already in Deluge session (idempotent grab for guid=%s)",
                        guid,
                    )
                    return True
                raise ProwlarrDownloadError(
                    f"Send to download client failed: HTTP {response.status_code} "
                    f"{body[:200]}"
                )
        except (ProwlarrDownloadError, ProwlarrConnectionError, ProwlarrOperationError):
            raise
        except Exception as exc:
            logger.error("Error sending torrent to download client: %s", exc)
            raise_mapped_httpx_error(
                exc,
                connection_error_type=ProwlarrConnectionError,
                operation_error_type=ProwlarrDownloadError,
                target=self._target(),
                operation="send torrent to download client",
            )
