"""Resolve Plex library guid (and rating key) from a watchlist media item."""
import logging

from app.domain.models.media import MediaItem, MediaType
from app.domain.models.plex_library_identity import PlexLibraryIdentity
from app.domain.ports.external.plex.plex_server_library_provider import (
    PlexServerLibraryProvider,
)
from app.domain.services.tmdb_guid import parse_tmdb_guid

logger = logging.getLogger(__name__)


class ResolvePlexLibraryIdentityQuery:
    def __init__(self, library_provider: PlexServerLibraryProvider):
        self._library_provider = library_provider

    async def execute(self, media: MediaItem) -> PlexLibraryIdentity | None:
        parsed = parse_tmdb_guid(media.guid or "")
        if parsed:
            media_type, tmdb_id = parsed
            identity = await self._library_provider.resolve_library_identity_for_tmdb_id(
                tmdb_id, media_type
            )
            if identity is None and media.title:
                identity = await self._library_provider.resolve_library_identity_by_title(
                    media.title,
                    media_type,
                    tmdb_id=tmdb_id,
                    year=media.year,
                )
            if identity is None:
                return None
            logger.debug(
                "Resolved Plex library identity for TMDB %s/%s: guid=%s",
                media_type,
                tmdb_id,
                identity.plex_guid,
            )
            return identity

        if media.type in (MediaType.SHOW, MediaType.TVSHOW, MediaType.MOVIE):
            if media.guid:
                rating_key = media.rating_key
                if not rating_key and media.type == MediaType.MOVIE:
                    rating_key = None
                return PlexLibraryIdentity(
                    plex_guid=media.guid,
                    rating_key=rating_key,
                )
        return None
