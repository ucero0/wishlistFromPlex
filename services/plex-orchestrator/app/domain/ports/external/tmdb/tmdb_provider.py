"""TMDB provider port (Protocol)."""
from typing import Protocol, Optional, Tuple

from app.domain.models.external_connection import ExternalConnectionStatus


class TMDBProvider(Protocol):
    """Protocol for TMDB movie/TV show information provider."""

    async def test_connection(self) -> ExternalConnectionStatus:
        """Probe TMDB API connectivity (non-throwing)."""
        ...

    async def get_original_title_and_language(
        self,
        title: str,
        year: int,
        media_type: str,
    ) -> Optional[Tuple[str, str]]:
        ...
