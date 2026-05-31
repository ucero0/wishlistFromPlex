"""Pure helpers for Plex watchlist download pipeline."""
import logging

from app.application.tmdb.queries.get_original_title_query import GetOriginalTitleFromTMDBQuery
from app.domain.models.tv_episode import TvEpisode
from app.domain.services.tv_episode_search_query import (
    format_tv_episode_name_search_query,
    format_tv_episode_search_query,
)

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

    def build_tv_episode_search_queries(
        self, watchlist, episode: TvEpisode
    ) -> list[str]:
        """Strictest first: SxxExx + episode name, then SxxExx only."""
        show = watchlist.title or ""
        if episode.name:
            return [
                format_tv_episode_name_search_query(
                    show, episode.season, episode.episode, episode.name
                ),
                format_tv_episode_search_query(
                    show, episode.season, episode.episode
                ),
            ]
        return [
            format_tv_episode_search_query(
                show, episode.season, episode.episode
            )
        ]
