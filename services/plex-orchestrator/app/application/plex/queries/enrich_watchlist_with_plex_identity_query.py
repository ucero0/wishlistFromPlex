"""Attach resolved Plex library guids to watchlist rows (especially TMDB-sourced)."""
import logging

from app.application.plex.queries.resolve_plex_library_identity_query import (
    ResolvePlexLibraryIdentityQuery,
)
from app.domain.models.media import MediaItem
from app.domain.models.watchlist_item_for_user import WatchlistItemForUser
from app.domain.models.watchlist_source import WatchlistSource

logger = logging.getLogger(__name__)


class EnrichWatchlistWithPlexIdentityQuery:
    def __init__(
        self,
        resolve_plex_library_identity_query: ResolvePlexLibraryIdentityQuery,
    ):
        self._resolve_plex_library_identity = resolve_plex_library_identity_query

    async def execute(
        self, entries: list[WatchlistItemForUser]
    ) -> list[WatchlistItemForUser]:
        enriched: list[WatchlistItemForUser] = []
        for entry in entries:
            enriched.append(await self._enrich_entry(entry))
        return enriched

    async def _enrich_entry(self, entry: WatchlistItemForUser) -> WatchlistItemForUser:
        if entry.source == WatchlistSource.PLEX:
            item = entry.item.model_copy(
                update={"plex_library_guid": entry.item.guid or None}
            )
            return entry.model_copy(update={"item": item})

        identity = await self._resolve_plex_library_identity.execute(entry.item)
        if identity is None:
            return entry

        logger.info(
            "Linked TMDB watchlist '%s' to Plex library guid %s",
            entry.item.title,
            identity.plex_guid,
        )
        item = entry.item.model_copy(
            update={
                "plex_library_guid": identity.plex_guid,
                "rating_key": identity.rating_key or entry.item.rating_key,
            }
        )
        return entry.model_copy(update={"item": item})
