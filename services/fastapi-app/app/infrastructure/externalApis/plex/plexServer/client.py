import logging
from typing import Any, Dict, Optional

import httpx

from app.core.config import settings
from app.domain.errors.plex import (
    PlexAuthError,
    PlexConnectionError,
    PlexOperationError,
)
from app.infrastructure.externalApis.plex.plexServer.schemas import (
    PlexLibraryAllResponse,
    PlexLibraryLocationItem,
    PlexLibraryLocationsByMediaResponse,
)
from app.domain.plex.library_media_type import normalize_plex_section_type
from app.infrastructure.http_errors import raise_mapped_httpx_error

logger = logging.getLogger(__name__)

PLEX_API_HEADERS = {
    "Accept": "application/json",
    "X-Plex-Client-Identifier": "plex-wishlist-service",
    "X-Plex-Product": "Plex Wishlist Service",
    "X-Plex-Version": "1.0.0",
}


class PlexServerLibraryApiClient:
    """Infrastructure client for Plex library API communication."""

    def __init__(self, token: str):
        self.plex_server_url = settings.plex_server_url
        self.plex_api_headers = PLEX_API_HEADERS
        self.url_library_search = f"{self.plex_server_url}/library/all"

    def _target(self) -> str:
        return self.plex_server_url

    async def test_connection(self) -> bool:
        """Probe Plex server reachability (no user token required)."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.plex_server_url}/identity",
                    headers=self.plex_api_headers,
                )
                return response.status_code == 200
        except Exception:
            return False

    def _build_params(
        self, guid: str, user_token: str, media_type: Optional[int] = None
    ) -> Dict[str, Any]:
        params = {"guid": guid, "X-Plex-Token": user_token}
        if media_type is not None:
            params["type"] = media_type
        return params

    def _raise_plex_http_error(self, exc: Exception, operation: str) -> None:
        if isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code in (
            401,
            403,
        ):
            raise PlexAuthError(
                f"{operation} unauthorized for {self._target()}"
            ) from exc
        raise_mapped_httpx_error(
            exc,
            connection_error_type=PlexConnectionError,
            operation_error_type=PlexOperationError,
            target=self._target(),
            operation=operation,
        )

    async def get_library_items_raw(
        self, user_token: str, guid: str, media_type: Optional[int] = None
    ) -> PlexLibraryAllResponse:
        params = self._build_params(guid, user_token, media_type)
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    self.url_library_search,
                    headers=self.plex_api_headers,
                    params=params,
                )
                response.raise_for_status()
                logger.debug("Plex library/all request completed successfully")
                response_json = response.json()
                return PlexLibraryAllResponse(
                    MediaContainer=response_json.get("MediaContainer", {})
                )
        except Exception as exc:
            self._raise_plex_http_error(exc, "library search")

    async def get_library_locations_by_media_raw(
        self, user_token: str
    ) -> PlexLibraryLocationsByMediaResponse:
        url = f"{self.plex_server_url}/library/sections"
        params = {"X-Plex-Token": user_token}
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    url,
                    headers=self.plex_api_headers,
                    params=params,
                )
                response.raise_for_status()
                logger.debug("Plex library/sections request completed successfully")
                response_json = response.json()
                directories = response_json.get("MediaContainer", {}).get(
                    "Directory", []
                )
                items = []
                for section in directories:
                    media_type = normalize_plex_section_type(section.get("type"))
                    locations = [
                        location.get("path")
                        for location in section.get("Location", [])
                        if location.get("path")
                    ]
                    items.append(
                        PlexLibraryLocationItem(
                            section_id=str(section.get("key")),
                            section_title=section.get("title") or "",
                            media_type=media_type,
                            locations=locations,
                        )
                    )
                return PlexLibraryLocationsByMediaResponse(items=items)
        except Exception as exc:
            self._raise_plex_http_error(exc, "list library sections")

    async def partial_scan_library_raw(
        self,
        user_token: str,
        section_id: int,
        folder_path: str,
    ) -> bool:
        url = f"{self.plex_server_url}/library/sections/{section_id}/refresh"
        params = {"X-Plex-Token": user_token, "path": folder_path}
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    url,
                    headers=self.plex_api_headers,
                    params=params,
                )
                response.raise_for_status()
                logger.info(
                    "Partial scan triggered for section %s, path: %s",
                    section_id,
                    folder_path,
                )
                return True
        except Exception as exc:
            self._raise_plex_http_error(
                exc, f"partial scan section {section_id}"
            )
