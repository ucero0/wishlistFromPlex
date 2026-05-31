"""Port for Plex server library provider."""
from typing import Protocol

from app.domain.models.external_connection import ExternalConnectionStatus
from app.domain.models.media import MediaItem
from app.domain.models.plex_library_identity import PlexLibraryIdentity
from app.domain.models.plex_library_locations import PlexLibraryLocationsByMedia
from app.domain.models.tv_episode import TvEpisode


class PlexServerLibraryProvider(Protocol):
    """Protocol for Plex server library operations (uses server admin token)."""

    async def test_connection(self) -> ExternalConnectionStatus:
        """Probe Plex server reachability (non-throwing)."""
        ...

    async def is_item_in_library(self, media: MediaItem) -> bool:
        ...

    async def is_tmdb_item_in_library(
        self, tmdb_id: int, media_type: str, media: MediaItem
    ) -> bool:
        ...

    async def resolve_show_guid_for_tmdb_id(self, tmdb_id: int) -> str | None:
        ...

    async def resolve_library_identity_for_tmdb_id(
        self, tmdb_id: int, media_type: str
    ) -> PlexLibraryIdentity | None:
        ...

    async def resolve_library_identity_by_title(
        self,
        title: str,
        media_type: str,
        *,
        tmdb_id: int | None = None,
        year: int | None = None,
    ) -> PlexLibraryIdentity | None:
        ...

    async def get_owned_show_episodes(self, show_guid: str) -> list[TvEpisode]:
        """Episodes present in the local Plex library for a show guid."""
        ...

    async def get_show_catalog_episodes(self, show_guid: str) -> list[TvEpisode]:
        """Season/episode tree from local Plex library metadata for a show guid."""
        ...

    async def get_watched_show_episodes(
        self, show_guid: str, user_token: str
    ) -> list[TvEpisode]:
        """Episodes watched or in-progress for one Plex user."""
        ...

    async def get_library_locations_by_media(self) -> PlexLibraryLocationsByMedia:
        ...

    async def partial_scan_library(
        self,
        section_id: int,
        folder_path: str,
    ) -> bool:
        ...
