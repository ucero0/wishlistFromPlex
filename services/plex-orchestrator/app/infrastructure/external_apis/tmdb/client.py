"""TMDB client - infrastructure layer."""
import logging
from typing import Optional, Union

import httpx

from app.core.config import settings
from app.domain.errors.tmdb import (
    TMDBConfigurationError,
    TMDBConnectionError,
    TMDBOperationError,
)
from app.infrastructure.external_apis.tmdb.schemas import (
    TMDBMovieResponse,
    TMDBMovieSearchResponse,
    TMDBTVResponse,
    TMDBTVSearchResponse,
)
from app.infrastructure.http_errors import raise_mapped_httpx_error

from app.infrastructure.external_apis.tmdb.jwt_utils import account_object_id_from_access_token

logger = logging.getLogger(__name__)

TMDB_API_BASE = "https://api.themoviedb.org/3"
TMDB_V4_API_BASE = "https://api.themoviedb.org/4"


class TMDBClient:
    """Infrastructure client for TMDB API."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = TMDB_API_BASE

    def _ensure_api_key(self) -> None:
        if not self.api_key or not str(self.api_key).strip():
            raise TMDBConfigurationError("TMDB API key is not configured")

    def _target(self) -> str:
        return self.base_url

    async def probe_connection(self) -> None:
        """Raise when TMDB API is unreachable or misconfigured."""
        self._ensure_api_key()
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.base_url}/configuration",
                    params={"api_key": self.api_key},
                )
                if response.status_code == 401:
                    raise TMDBConfigurationError("TMDB API key is invalid or unauthorized")
                response.raise_for_status()
        except TMDBConfigurationError:
            raise
        except Exception as exc:
            raise_mapped_httpx_error(
                exc,
                connection_error_type=TMDBConnectionError,
                operation_error_type=TMDBOperationError,
                target=self._target(),
                operation="connection probe",
                auth_error_type=TMDBConfigurationError,
            )

    async def get_movie(self, tmdb_id: int) -> TMDBMovieResponse:
        self._ensure_api_key()
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.base_url}/movie/{tmdb_id}",
                    params={"api_key": self.api_key},
                )
                response.raise_for_status()
                return TMDBMovieResponse(**response.json())
        except (TMDBConfigurationError, TMDBConnectionError, TMDBOperationError):
            raise
        except Exception as exc:
            raise_mapped_httpx_error(
                exc,
                connection_error_type=TMDBConnectionError,
                operation_error_type=TMDBOperationError,
                target=self._target(),
                operation=f"get movie {tmdb_id}",
            )

    async def get_tv_show(self, tmdb_id: int) -> TMDBTVResponse:
        self._ensure_api_key()
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.base_url}/tv/{tmdb_id}",
                    params={"api_key": self.api_key},
                )
                response.raise_for_status()
                return TMDBTVResponse(**response.json())
        except (TMDBConfigurationError, TMDBConnectionError, TMDBOperationError):
            raise
        except Exception as exc:
            raise_mapped_httpx_error(
                exc,
                connection_error_type=TMDBConnectionError,
                operation_error_type=TMDBOperationError,
                target=self._target(),
                operation=f"get tv show {tmdb_id}",
            )

    async def search(
        self,
        title: str,
        year: Optional[int] = None,
        media_type: str = "movie",
    ) -> Optional[Union[TMDBMovieResponse, TMDBTVResponse]]:
        """
        Search TMDB by title/year.
        Returns None when no match is found (valid business outcome).
        """
        self._ensure_api_key()
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                params = {"api_key": self.api_key, "query": title}
                if media_type == "movie":
                    endpoint = f"{self.base_url}/search/movie"
                    if year:
                        params["year"] = year
                else:
                    endpoint = f"{self.base_url}/search/tv"
                    if year:
                        params["first_air_date_year"] = year

                response = await client.get(endpoint, params=params)
                response.raise_for_status()

                if media_type == "movie":
                    search_response = TMDBMovieSearchResponse(**response.json())
                    if search_response.results:
                        return await self.get_movie(search_response.results[0].id)
                else:
                    search_response = TMDBTVSearchResponse(**response.json())
                    if search_response.results:
                        return await self.get_tv_show(search_response.results[0].id)
                return None
        except (TMDBConfigurationError, TMDBConnectionError, TMDBOperationError):
            raise
        except Exception as exc:
            raise_mapped_httpx_error(
                exc,
                connection_error_type=TMDBConnectionError,
                operation_error_type=TMDBOperationError,
                target=self._target(),
                operation=f"search {media_type}",
            )

    def _auth_headers(self, access_token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {access_token}"}

    async def get_account(self, access_token: str) -> "TMDBAccountResponse":
        from app.infrastructure.external_apis.tmdb.schemas import TMDBAccountResponse

        self._ensure_api_key()
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.base_url}/account",
                    params={"api_key": self.api_key},
                    headers=self._auth_headers(access_token),
                )
                response.raise_for_status()
                return TMDBAccountResponse(**response.json())
        except (TMDBConfigurationError, TMDBConnectionError, TMDBOperationError):
            raise
        except Exception as exc:
            raise_mapped_httpx_error(
                exc,
                connection_error_type=TMDBConnectionError,
                operation_error_type=TMDBOperationError,
                target=self._target(),
                operation="get account",
            )

    def _account_object_id(self, access_token: str) -> str:
        account_object_id = account_object_id_from_access_token(access_token)
        if not account_object_id:
            raise TMDBOperationError(
                "TMDB access token is missing a valid account object id (sub claim)"
            )
        return account_object_id

    async def get_watchlist(
        self, account_id: int, access_token: str
    ) -> list["TMDBWatchlistItem"]:
        from app.infrastructure.external_apis.tmdb.schemas import (
            TMDBWatchlistItem,
            TMDBWatchlistResponse,
        )

        self._ensure_api_key()
        account_object_id = self._account_object_id(access_token)
        items: list[TMDBWatchlistItem] = []
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                for media_type, path in (
                    ("movie", "movie/watchlist"),
                    ("tv", "tv/watchlist"),
                ):
                    page = 1
                    total_pages = 1
                    while page <= total_pages:
                        response = await client.get(
                            f"{TMDB_V4_API_BASE}/account/{account_object_id}/{path}",
                            params={"api_key": self.api_key, "page": page},
                            headers=self._auth_headers(access_token),
                        )
                        response.raise_for_status()
                        payload = TMDBWatchlistResponse(**response.json())
                        for raw in payload.results:
                            item = raw.model_copy(update={"media_type": media_type})
                            items.append(item)
                        total_pages = max(payload.total_pages, 1)
                        page += 1
                return items
        except (TMDBConfigurationError, TMDBConnectionError, TMDBOperationError):
            raise
        except Exception as exc:
            raise_mapped_httpx_error(
                exc,
                connection_error_type=TMDBConnectionError,
                operation_error_type=TMDBOperationError,
                target=self._target(),
                operation=f"get watchlist for account {account_id}",
            )

    async def remove_from_watchlist(
        self,
        account_id: int,
        access_token: str,
        media_type: str,
        media_id: int,
    ) -> None:
        self._ensure_api_key()
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.base_url}/account/{account_id}/watchlist",
                    params={"api_key": self.api_key},
                    headers=self._auth_headers(access_token),
                    json={
                        "media_type": media_type,
                        "media_id": media_id,
                        "watchlist": False,
                    },
                )
                response.raise_for_status()
        except (TMDBConfigurationError, TMDBConnectionError, TMDBOperationError):
            raise
        except Exception as exc:
            raise_mapped_httpx_error(
                exc,
                connection_error_type=TMDBConnectionError,
                operation_error_type=TMDBOperationError,
                target=self._target(),
                operation=f"remove {media_type}/{media_id} from watchlist",
            )

    async def add_to_watchlist(
        self,
        account_id: int,
        access_token: str,
        media_type: str,
        media_id: int,
    ) -> None:
        self._ensure_api_key()
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.base_url}/account/{account_id}/watchlist",
                    params={"api_key": self.api_key},
                    headers=self._auth_headers(access_token),
                    json={
                        "media_type": media_type,
                        "media_id": media_id,
                        "watchlist": True,
                    },
                )
                response.raise_for_status()
        except (TMDBConfigurationError, TMDBConnectionError, TMDBOperationError):
            raise
        except Exception as exc:
            raise_mapped_httpx_error(
                exc,
                connection_error_type=TMDBConnectionError,
                operation_error_type=TMDBOperationError,
                target=self._target(),
                operation=f"add {media_type}/{media_id} to watchlist",
            )

    async def get_tv_season(
        self, tv_id: int, season_number: int
    ) -> "TMDBSeasonDetailsResponse":
        from app.infrastructure.external_apis.tmdb.schemas import TMDBSeasonDetailsResponse

        self._ensure_api_key()
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    f"{self.base_url}/tv/{tv_id}/season/{season_number}",
                    params={"api_key": self.api_key},
                )
                response.raise_for_status()
                return TMDBSeasonDetailsResponse(**response.json())
        except (TMDBConfigurationError, TMDBConnectionError, TMDBOperationError):
            raise
        except Exception as exc:
            raise_mapped_httpx_error(
                exc,
                connection_error_type=TMDBConnectionError,
                operation_error_type=TMDBOperationError,
                target=self._target(),
                operation=f"get tv/{tv_id}/season/{season_number}",
            )
