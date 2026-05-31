"""Compare TMDB catalog episodes with owned and queued episodes."""
import logging

from app.application.plex.queries.get_latest_watched_episode_for_show_query import (
    GetLatestWatchedEpisodeForShowQuery,
)
from app.application.plex.queries.get_owned_show_episodes_query import (
    GetOwnedShowEpisodesQuery,
)
from app.application.plex.queries.get_show_catalog_episodes_query import (
    GetShowCatalogEpisodesQuery,
)
from app.application.pipelines.watchlist.queries.is_episode_already_queued_query import (
    IsEpisodeAlreadyQueuedQuery,
)
from app.core.config import settings
from app.domain.models.media import MediaItem
from app.domain.models.tv_episode import TvEpisode
from app.domain.services.media_library_guid import library_guid_for_media
from app.domain.services.tv_download_buffer import filter_missing_for_ahead_buffer

logger = logging.getLogger(__name__)


class GetMissingTvEpisodesQuery:
    def __init__(
        self,
        get_catalog_episodes_query: GetShowCatalogEpisodesQuery,
        get_owned_episodes_query: GetOwnedShowEpisodesQuery,
        is_episode_already_queued_query: IsEpisodeAlreadyQueuedQuery,
        get_latest_watched_episode_query: GetLatestWatchedEpisodeForShowQuery,
    ):
        self._get_catalog_episodes_query = get_catalog_episodes_query
        self._get_owned_episodes_query = get_owned_episodes_query
        self._is_episode_already_queued_query = is_episode_already_queued_query
        self._get_latest_watched_episode_query = get_latest_watched_episode_query

    async def execute(
        self,
        watchlist: MediaItem,
        user_token: str,
        *,
        plex_user_token: str | None = None,
        for_download: bool = False,
    ) -> list[TvEpisode]:
        catalog = await self._get_catalog_episodes_query.execute(
            watchlist, user_token, plex_user_token=plex_user_token
        )
        if not catalog:
            logger.warning(
                "No episode catalog found for show '%s'", watchlist.title
            )
            return []

        owned = {
            (ep.season, ep.episode)
            for ep in await self._get_owned_episodes_query.execute(
                library_guid_for_media(watchlist)
            )
        }

        missing: list[TvEpisode] = []
        for episode in catalog:
            key = (episode.season, episode.episode)
            if key in owned:
                continue
            if await self._is_episode_already_queued_query.execute_for_watchlist(
                watchlist, episode
            ):
                continue
            missing.append(episode)

        if not for_download:
            return missing

        latest_watched = await self._get_latest_watched_episode_query.execute(
            library_guid_for_media(watchlist)
        )
        buffered = filter_missing_for_ahead_buffer(
            catalog,
            missing,
            latest_watched,
            ahead_episodes=settings.tv_watchlist_ahead_episodes,
        )
        if latest_watched is None:
            logger.info(
                "No watch progress for '%s'; %s episode(s) in first-%s catalog buffer",
                watchlist.title,
                len(buffered),
                settings.tv_watchlist_ahead_episodes,
            )
        else:
            logger.info(
                "Watch progress for '%s' at S%02dE%02d; %s episode(s) in ahead buffer",
                watchlist.title,
                latest_watched.season,
                latest_watched.episode,
                len(buffered),
            )
        return buffered
