"""Find the furthest watched episode for a show across all active Plex users."""
import logging

from app.application.plex.queries.get_plex_users_query import GetPlexUserQuery
from app.domain.models.tv_episode import TvEpisode
from app.domain.ports.external.plex.plex_server_library_provider import (
    PlexServerLibraryProvider,
)
from app.domain.services.tmdb_guid import parse_tmdb_guid
from app.domain.services.tv_download_buffer import max_watched_episode

logger = logging.getLogger(__name__)


class GetLatestWatchedEpisodeForShowQuery:
    def __init__(
        self,
        library_provider: PlexServerLibraryProvider,
        get_plex_user_query: GetPlexUserQuery,
    ):
        self._library_provider = library_provider
        self._get_plex_user_query = get_plex_user_query

    async def execute(self, show_guid: str) -> TvEpisode | None:
        resolved_guid = show_guid
        parsed = parse_tmdb_guid(show_guid)
        if parsed:
            _, tmdb_id = parsed
            plex_guid = await self._library_provider.resolve_show_guid_for_tmdb_id(
                tmdb_id
            )
            if not plex_guid:
                return None
            resolved_guid = plex_guid

        users = await self._get_plex_user_query.execute()
        latest: TvEpisode | None = None

        for user in users:
            watched = await self._library_provider.get_watched_show_episodes(
                resolved_guid, user.plex_token
            )
            user_latest = max_watched_episode(watched)
            if user_latest is None:
                continue
            if latest is None or (
                user_latest.season,
                user_latest.episode,
            ) > (latest.season, latest.episode):
                latest = user_latest
                logger.debug(
                    "Latest watched for show %s is now S%02dE%02d (user=%s)",
                    show_guid,
                    latest.season,
                    latest.episode,
                    user.name,
                )

        if latest:
            logger.info(
                "Furthest watch progress for show %s: S%02dE%02d",
                show_guid,
                latest.season,
                latest.episode,
            )
        return latest
