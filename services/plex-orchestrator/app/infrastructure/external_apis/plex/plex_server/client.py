import logging
from typing import Any, Dict, Optional

import httpx

from app.application.plex.services.plex_server_admin_token_resolver import (
    PlexServerAdminTokenResolver,
    plex_server_admin_token_resolver,
)
from app.core.config import settings
from app.domain.errors.plex import (
    PlexConnectionError,
    PlexOperationError,
    PlexServerAuthError,
)
from app.infrastructure.external_apis.plex.plex_server.schemas import (
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

    def __init__(
        self,
        token_resolver: PlexServerAdminTokenResolver | None = None,
    ) -> None:
        self._token_resolver = token_resolver or plex_server_admin_token_resolver
        self.plex_server_url = settings.plex_server_url
        self.plex_api_headers = PLEX_API_HEADERS
        self.url_library_search = f"{self.plex_server_url}/library/all"

    def _target(self) -> str:
        return self.plex_server_url

    async def _admin_token(self, override: str | None = None) -> str:
        if override is not None and override.strip():
            return override.strip()
        return await self._token_resolver.resolve()

    async def _build_params(
        self,
        guid: str,
        media_type: Optional[int] = None,
        *,
        admin_token: str | None = None,
    ) -> Dict[str, Any]:
        params = {
            "guid": guid,
            "X-Plex-Token": await self._admin_token(admin_token),
        }
        if media_type is not None:
            params["type"] = media_type
        return params

    def _raise_plex_http_error(
        self,
        exc: Exception,
        operation: str,
        *,
        map_auth: bool = True,
    ) -> None:
        auth_error_type = PlexServerAuthError if map_auth else None
        if map_auth and isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code in (
            401,
            403,
        ):
            raise PlexServerAuthError(
                f"{operation} unauthorized: Plex server admin token is invalid or "
                f"does not have access to Plex server at {self._target()}"
            ) from exc
        raise_mapped_httpx_error(
            exc,
            connection_error_type=PlexConnectionError,
            operation_error_type=PlexOperationError,
            target=self._target(),
            operation=operation,
            auth_error_type=auth_error_type,
        )

    async def probe_connection(self) -> None:
        """Raise when Plex server is unreachable (no admin token required)."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.plex_server_url}/identity",
                    headers=self.plex_api_headers,
                )
                response.raise_for_status()
        except Exception as exc:
            self._raise_plex_http_error(exc, "connection probe", map_auth=False)

    async def validate_admin_token(self, admin_token: str) -> None:
        """Probe library/sections with a candidate token before persisting it."""
        await self.get_library_locations_by_media_raw(admin_token=admin_token)

    async def get_library_items_raw(
        self,
        guid: str,
        media_type: Optional[int] = None,
        *,
        admin_token: str | None = None,
    ) -> PlexLibraryAllResponse:
        params = await self._build_params(guid, media_type, admin_token=admin_token)
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
        self,
        *,
        admin_token: str | None = None,
    ) -> PlexLibraryLocationsByMediaResponse:
        url = f"{self.plex_server_url}/library/sections"
        params = {"X-Plex-Token": await self._admin_token(admin_token)}
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
        section_id: int,
        folder_path: str,
    ) -> bool:
        url = f"{self.plex_server_url}/library/sections/{section_id}/refresh"
        params = {
            "X-Plex-Token": await self._admin_token(),
            "path": folder_path,
        }
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
