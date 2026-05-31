"""Check whether a TV episode is already downloading or deferred."""
from app.domain.models.media import MediaItem
from app.domain.models.tv_episode import TvEpisode
from app.domain.services.media_library_guid import library_guid_for_media
from app.domain.ports.repositories.active_downloads.active_download_repository_port import (
    ActiveDownloadRepositoryPort,
)
from app.domain.ports.repositories.deferred_downloads.deferred_download_repository_port import (
    DeferredDownloadRepositoryPort,
)
from app.domain.services.tv_episode_search_query import parse_season_episode


class IsEpisodeAlreadyQueuedQuery:
    def __init__(
        self,
        torrent_repo: ActiveDownloadRepositoryPort,
        deferred_repo: DeferredDownloadRepositoryPort,
    ):
        self._torrent_repo = torrent_repo
        self._deferred_repo = deferred_repo

    async def execute_for_watchlist(
        self,
        watchlist: MediaItem,
        episode: TvEpisode,
    ) -> bool:
        guids = {
            g
            for g in (
                watchlist.guid,
                watchlist.plex_library_guid,
                library_guid_for_media(watchlist),
            )
            if g
        }
        for guid in guids:
            if await self.execute(guid, watchlist.title or "", episode):
                return True
        return False

    async def execute(
        self,
        plex_guid: str,
        title: str,
        episode: TvEpisode,
    ) -> bool:
        if await self._torrent_repo.has_episode_queued(
            plex_guid, title, episode.season, episode.episode
        ):
            return True

        for pending in await self._deferred_repo.list_pending_by_guid_plex(plex_guid):
            parsed = parse_season_episode(pending.search_query or "")
            if parsed == episode:
                return True
        return False
