"""Pure helpers for Plex watchlist download pipeline."""
import logging

from app.application.tmdb.queries.get_original_title_query import GetOriginalTitleFromTMDBQuery
from app.domain.services.tv_episode_search_query import format_tv_episode_search_query

logger = logging.getLogger(__name__)


def watchlist_media_type(watchlist) -> str | None:
    if watchlist.type is None:
        return None
    if hasattr(watchlist.type, "value"):
        return str(watchlist.type.value)
    return str(watchlist.type)


def is_show_watchlist(watchlist) -> bool:
    media_type = watchlist_media_type(watchlist)
    return media_type in ("show", "tvshow")


class WatchlistSearchQueryBuilder:
    """Build a Prowlarr search string, using TMDB original title for Spanish movies."""

    def __init__(self, get_original_title_query: GetOriginalTitleFromTMDBQuery):
        self._get_original_title_query = get_original_title_query

    async def execute(self, watchlist) -> str:
        tmdb_result = await self._get_original_title_query.execute(watchlist)
        if tmdb_result:
            original_title, original_language = tmdb_result
            if original_language == "es":
                logger.info(
                    "Using original title '%s' for Spanish movie '%s' (original_language: %s)",
                    original_title,
                    watchlist.title,
                    original_language,
                )
                return f"{original_title} {watchlist.year}"
        return f"{watchlist.title} {watchlist.year}"

    def build_tv_episode_search_query(
        self, watchlist, season: int, episode: int
    ) -> str:
        return format_tv_episode_search_query(
            watchlist.title or "", season, episode
        )
