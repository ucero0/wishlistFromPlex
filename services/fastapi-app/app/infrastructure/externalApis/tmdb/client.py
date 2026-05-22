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
from app.infrastructure.externalApis.tmdb.schemas import (
    TMDBMovieResponse,
    TMDBMovieSearchResponse,
    TMDBTVResponse,
    TMDBTVSearchResponse,
)
from app.infrastructure.http_errors import raise_mapped_httpx_error

logger = logging.getLogger(__name__)

TMDB_API_BASE = "https://api.themoviedb.org/3"


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

    async def test_connection(self) -> bool:
        """Probe TMDB API using the configuration endpoint."""
        if not self.api_key or not str(self.api_key).strip():
            return False
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.base_url}/configuration",
                    params={"api_key": self.api_key},
                )
                return response.status_code == 200
        except Exception:
            return False

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
