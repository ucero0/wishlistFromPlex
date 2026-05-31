"""Load a TV show episode catalog from the local Plex library metadata tree."""
import logging

from app.domain.models.tv_episode import TvEpisode
from app.domain.ports.external.plex.plex_server_library_provider import (
    PlexServerLibraryProvider,
)
from app.domain.services.tmdb_guid import parse_tmdb_guid

logger = logging.getLogger(__name__)


class GetPlexServerShowCatalogEpisodesQuery:
    def __init__(self, library_provider: PlexServerLibraryProvider):
        self._library_provider = library_provider

    async def execute(self, show_guid: str) -> list[TvEpisode]:
        parsed = parse_tmdb_guid(show_guid)
        if parsed:
            _, tmdb_id = parsed
            identity = await self._library_provider.resolve_library_identity_for_tmdb_id(
                tmdb_id, "tv"
            )
            if identity is None:
                return []
            show_guid = identity.plex_guid

        episodes = await self._library_provider.get_show_catalog_episodes(show_guid)
        if episodes:
            logger.info(
                "Loaded Plex server catalog for show guid %s (%s episodes)",
                show_guid,
                len(episodes),
            )
        return sorted(episodes, key=lambda ep: (ep.season, ep.episode))
