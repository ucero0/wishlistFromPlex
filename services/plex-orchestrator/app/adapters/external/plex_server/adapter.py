"""Adapter for Plex server library API."""
import logging

from app.adapters.external.plex_server import mapper as plex_server_mapper
from app.adapters.external.plex.tv_episode_mapper import (
    crawl_show_episodes_from_server,
    crawl_watched_show_episodes_from_server,
    resolve_show_rating_key_from_server,
)
from app.domain.models.external_connection import ExternalConnectionStatus
from app.domain.models.media import MediaItem
from app.domain.models.plex_library_locations import PlexLibraryLocationsByMedia
from app.domain.models.plex_library_identity import PlexLibraryIdentity
from app.domain.services.plex_metadata_guids import metadata_matches_tmdb_id
from app.domain.services.tmdb_guid import build_tmdb_movie_guid, build_tmdb_tv_guid
from app.domain.models.tv_episode import TvEpisode
from app.domain.ports.external.plex.plex_server_library_provider import (
    PlexServerLibraryProvider,
)
from app.domain.services.connection_probe import capture_async_connection_probe
from app.infrastructure.external_apis.plex.plex_server.client import (
    PlexServerLibraryApiClient,
)

logger = logging.getLogger(__name__)


class PlexServerLibraryAdapter(PlexServerLibraryProvider):
    """Adapter that converts between Plex infrastructure and domain models."""

    def __init__(self, client: PlexServerLibraryApiClient):
        self.client = client

    async def test_connection(self) -> ExternalConnectionStatus:
        return await capture_async_connection_probe(
            "plex",
            self.client.probe_connection,
        )

    async def is_item_in_library(self, media: MediaItem) -> bool:
        logger.info(
            "Checking if item is in library: guid=%s, type=%s", media.guid, media.type
        )
        media_int = None
        if media.type == "movie":
            media_int = 1
        elif media.type == "show":
            media_int = 2
        else:
            logger.warning("Unknown media type: %s, will not filter by type", media.type)

        response = await self.client.get_library_items_raw(media.guid, media_int)
        media_container = response.MediaContainer
        size = int(media_container.get("size", 0))
        if size == 1:
            metadata = media_container.get("Metadata", [])
            if metadata and metadata[0].get("guid") == media.guid:
                return True
            return False
        return False

    async def is_tmdb_item_in_library(
        self, tmdb_id: int, media_type: str, media: MediaItem
    ) -> bool:
        identity = await self.resolve_library_identity_for_tmdb_id(tmdb_id, media_type)
        if identity is not None:
            return True
        if media.title:
            identity = await self.resolve_library_identity_by_title(
                media.title,
                media_type,
                tmdb_id=tmdb_id,
                year=media.year,
            )
            return identity is not None
        return False

    async def resolve_show_guid_for_tmdb_id(self, tmdb_id: int) -> str | None:
        identity = await self.resolve_library_identity_for_tmdb_id(tmdb_id, "tv")
        if identity is None:
            return None
        return identity.plex_guid

    async def resolve_library_identity_for_tmdb_id(
        self, tmdb_id: int, media_type: str
    ) -> PlexLibraryIdentity | None:
        media_int = 1 if media_type == "movie" else 2 if media_type == "tv" else None
        if media_int is None:
            return None

        guid_candidates = [
            build_tmdb_movie_guid(tmdb_id) if media_type == "movie" else build_tmdb_tv_guid(tmdb_id),
            f"tmdb://{tmdb_id}",
            *self._tmdb_agent_guids(tmdb_id, media_type),
        ]
        for guid in guid_candidates:
            response = await self.client.get_library_items_raw(
                guid, media_type=media_int
            )
            if int(response.MediaContainer.get("size", 0)) < 1:
                continue
            metadata = response.MediaContainer.get("Metadata") or []
            if not metadata:
                continue
            identity = self._identity_from_metadata_row(metadata[0])
            if identity is not None:
                return identity
        return None

    async def resolve_library_identity_by_title(
        self,
        title: str,
        media_type: str,
        *,
        tmdb_id: int | None = None,
        year: int | None = None,
    ) -> PlexLibraryIdentity | None:
        media_int = 1 if media_type == "movie" else 2 if media_type == "tv" else None
        if media_int is None or not title.strip():
            return None

        response = await self.client.search_library_by_title_raw(
            title.strip(), media_int, year=year
        )
        candidates = response.MediaContainer.get("Metadata") or []
        if not candidates:
            logger.debug(
                "No Plex library title match for '%s' (%s)", title, media_type
            )
            return None

        if tmdb_id is not None:
            for row in candidates:
                identity = await self._identity_if_row_matches_tmdb(
                    row, tmdb_id, media_type
                )
                if identity is not None:
                    logger.info(
                        "Resolved Plex library identity for '%s' via title search "
                        "(TMDB %s/%s): guid=%s",
                        title,
                        media_type,
                        tmdb_id,
                        identity.plex_guid,
                    )
                    return identity

        if len(candidates) == 1:
            identity = self._identity_from_metadata_row(candidates[0])
            if identity is not None:
                logger.info(
                    "Resolved Plex library identity for '%s' via title search: guid=%s",
                    title,
                    identity.plex_guid,
                )
                return identity

        if year is not None:
            for row in candidates:
                if row.get("year") == year:
                    identity = self._identity_from_metadata_row(row)
                    if identity is not None:
                        return identity

        logger.debug(
            "Ambiguous Plex title matches for '%s' (%s candidates)",
            title,
            len(candidates),
        )
        return None

    async def _identity_if_row_matches_tmdb(
        self, row: dict, tmdb_id: int, media_type: str
    ) -> PlexLibraryIdentity | None:
        rating_key = row.get("ratingKey")
        if not rating_key:
            return None
        if metadata_matches_tmdb_id(row, tmdb_id, media_type):
            return self._identity_from_metadata_row(row)

        raw = await self.client.get_metadata_raw(str(rating_key))
        metadata = raw.get("MediaContainer", {}).get("Metadata") or []
        if not metadata:
            return None
        full = metadata[0]
        if metadata_matches_tmdb_id(full, tmdb_id, media_type):
            return self._identity_from_metadata_row(full)
        return None

    @staticmethod
    def _identity_from_metadata_row(row: dict) -> PlexLibraryIdentity | None:
        plex_guid = row.get("guid")
        if not plex_guid:
            return None
        rating_key = row.get("ratingKey")
        return PlexLibraryIdentity(
            plex_guid=str(plex_guid),
            rating_key=str(rating_key) if rating_key else None,
        )

    @staticmethod
    def _tmdb_agent_guids(tmdb_id: int, media_type: str) -> list[str]:
        return [
            f"com.plexapp.agents.themoviedb://{media_type}/{tmdb_id}?lang=en",
            f"com.plexapp.agents.themoviedb://{media_type}/{tmdb_id}",
            f"com.plexapp.agents.tmdb://{media_type}/{tmdb_id}?lang=en",
        ]

    async def get_owned_show_episodes(self, show_guid: str) -> list[TvEpisode]:
        response = await self.client.get_library_items_raw(show_guid, media_type=2)
        media_container = response.MediaContainer
        if int(media_container.get("size", 0)) != 1:
            return []
        metadata = media_container.get("Metadata") or []
        if not metadata:
            return []
        show = metadata[0]
        if show.get("guid") != show_guid:
            return []
        rating_key = show.get("ratingKey")
        if not rating_key:
            return []
        return await crawl_show_episodes_from_server(self.client, str(rating_key))

    async def get_show_catalog_episodes(self, show_guid: str) -> list[TvEpisode]:
        """Season/episode tree from local Plex library metadata for this show."""
        return await self.get_owned_show_episodes(show_guid)

    async def get_watched_show_episodes(
        self, show_guid: str, user_token: str
    ) -> list[TvEpisode]:
        rating_key = await resolve_show_rating_key_from_server(
            self.client, show_guid, user_token=user_token
        )
        if not rating_key:
            return []
        return await crawl_watched_show_episodes_from_server(
            self.client, rating_key, user_token
        )

    async def get_library_locations_by_media(
        self,
    ) -> PlexLibraryLocationsByMedia:
        raw = await self.client.get_library_locations_by_media_raw()
        return plex_server_mapper.library_locations_response_to_domain(raw)

    async def partial_scan_library(
        self,
        section_id: int,
        folder_path: str,
    ) -> bool:
        return await self.client.partial_scan_library_raw(section_id, folder_path)
