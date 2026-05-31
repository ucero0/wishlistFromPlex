import logging
from typing import Any, Dict

import httpx

from app.domain.errors.plex import PlexConnectionError, PlexOperationError, PlexUserAuthError
from app.infrastructure.http_errors import raise_mapped_httpx_error

logger = logging.getLogger(__name__)

PLEX_DISCOVER_API = "https://discover.provider.plex.tv"

DEFAULT_HEADERS = {
    "Accept": "application/json",
    "X-Plex-Client-Identifier": "plex-wishlist-service",
    "X-Plex-Product": "Plex Wishlist Service",
    "X-Plex-Version": "1.0.0",
}


class PlexWatchlistClient:
    def _headers(self, user_token: str) -> Dict[str, Any]:
        return {**DEFAULT_HEADERS, "X-Plex-Token": user_token}

    def _target(self) -> str:
        return PLEX_DISCOVER_API

    def _raise_plex_http_error(self, exc: Exception, operation: str) -> None:
        if isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code in (
            401,
            403,
        ):
            raise PlexUserAuthError(
                f"{operation} unauthorized: Plex user token is invalid or expired"
            ) from exc
        raise_mapped_httpx_error(
            exc,
            connection_error_type=PlexConnectionError,
            operation_error_type=PlexOperationError,
            target=self._target(),
            operation=operation,
        )

    async def get_watchlist_raw(self, user_token: str) -> Dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{PLEX_DISCOVER_API}/library/sections/watchlist/all",
                    headers=self._headers(user_token),
                )
                response.raise_for_status()
                return response.json()
        except Exception as exc:
            self._raise_plex_http_error(exc, "get watchlist")

    async def add_item_raw(self, rating_key: str, user_token: str) -> None:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.put(
                    f"{PLEX_DISCOVER_API}/actions/addToWatchlist",
                    params={"ratingKey": rating_key},
                    headers=self._headers(user_token),
                )
                response.raise_for_status()
        except Exception as exc:
            self._raise_plex_http_error(exc, "add watchlist item")

    async def delete_item_raw(self, rating_key: str, user_token: str) -> None:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.put(
                    f"{PLEX_DISCOVER_API}/actions/removeFromWatchlist",
                    params={"ratingKey": rating_key},
                    headers=self._headers(user_token),
                )
                response.raise_for_status()
        except Exception as exc:
            self._raise_plex_http_error(exc, "remove watchlist item")

    async def get_metadata_raw(
        self, rating_key: str, user_token: str
    ) -> Dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{PLEX_DISCOVER_API}/library/metadata/{rating_key}",
                    headers=self._headers(user_token),
                )
                response.raise_for_status()
                return response.json()
        except Exception as exc:
            self._raise_plex_http_error(exc, "get discover metadata")

    async def get_metadata_children_raw(
        self, rating_key: str, user_token: str
    ) -> Dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{PLEX_DISCOVER_API}/library/metadata/{rating_key}/children",
                    headers=self._headers(user_token),
                )
                response.raise_for_status()
                return response.json()
        except Exception as exc:
            self._raise_plex_http_error(exc, "get discover metadata children")
