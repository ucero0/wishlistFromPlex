"""Re-search Prowlarr and send a replacement torrent for an existing active download."""
import logging

from app.application.active_downloads.services.send_torrent_to_deluge_service import (
    SendTorrentToDelugeService,
)
from app.application.active_downloads.use_cases.update_active_download_use_case import (
    UpdateActiveDownloadUseCase,
)
from app.application.blacklist_torrent.queries import IsBlacklistedByGuidProwlarrQuery
from app.application.blacklist_torrent.use_cases import AddTorrentToBlacklistUseCase
from app.application.deferred_downloads.use_cases.enqueue_deferred_download_use_case import (
    EnqueueDeferredDownloadUseCase,
)
from app.application.pipelines.ingest.models.retry_active_download_outcome import (
    RetryActiveDownloadOutcome,
)
from app.application.pipelines.watchlist.services.watchlist_search_builder import (
    WatchlistSearchQueryBuilder,
)
from app.application.prowlarr.queries.find_best_torrent_query import GetBestTorrentsQuery
from app.domain.models.active_download import ActiveDownload
from app.domain.models.tv_episode import TvEpisode
from app.domain.ports.external.deluge.deluge_provider import DelugeProvider
from app.domain.services.download_volume_space_checker import DownloadVolumeSpaceChecker
from app.domain.services.torrent_infohash import (
    infohash_from_release,
    normalize_infohash,
)
from app.domain.services.tv_episode_search_query import (
    format_tv_episode_name_search_query,
    format_tv_episode_search_query,
)
from app.domain.services.watchlist_download_tracking import (
    watchlist_item_from_active_download,
)

logger = logging.getLogger(__name__)


class RetryActiveDownloadUseCase:
    def __init__(
        self,
        find_best_torrent_query: GetBestTorrentsQuery,
        is_blacklisted_query: IsBlacklistedByGuidProwlarrQuery,
        download_volume_space_checker: DownloadVolumeSpaceChecker,
        enqueue_deferred_use_case: EnqueueDeferredDownloadUseCase,
        send_torrent_to_deluge_service: SendTorrentToDelugeService,
        update_active_download_use_case: UpdateActiveDownloadUseCase,
        add_torrent_to_blacklist_use_case: AddTorrentToBlacklistUseCase,
        deluge_provider: DelugeProvider,
        watchlist_search_query_builder: WatchlistSearchQueryBuilder | None = None,
    ):
        self._find_best_torrent_query = find_best_torrent_query
        self._is_blacklisted_query = is_blacklisted_query
        self._download_volume_space_checker = download_volume_space_checker
        self._enqueue_deferred_use_case = enqueue_deferred_use_case
        self._send_torrent_to_deluge_service = send_torrent_to_deluge_service
        self._update_active_download_use_case = update_active_download_use_case
        self._add_torrent_to_blacklist = add_torrent_to_blacklist_use_case
        self._deluge_provider = deluge_provider
        self._watchlist_search_query_builder = watchlist_search_query_builder

    async def execute(
        self,
        active: ActiveDownload,
        *,
        blacklist_reason: str = "unhealthy",
    ) -> RetryActiveDownloadOutcome:
        excluded_hash = normalize_infohash(active.uid)
        media_type = "tv" if active.type in ("show", "tvshow") else "movie"
        search_queries = await self._search_queries(active, media_type=media_type)

        torrent_results = []
        search_query = ""
        for query in search_queries:
            torrent_results = await self._find_best_torrent_query.execute(
                query,
                media_type=media_type,
                show_year=active.year if media_type == "tv" else None,
            )
            if torrent_results:
                search_query = query
                break

        if not torrent_results:
            logger.warning(
                "No replacement torrent for '%s' (tried: %s)",
                active.title,
                search_queries,
            )
            return RetryActiveDownloadOutcome.NO_TORRENT

        entry = watchlist_item_from_active_download(active)
        season = active.season
        episode = active.episode
        episode_name = active.episode_name

        for index, torrent_result in enumerate(torrent_results):
            guid = torrent_result.guid
            if not guid:
                continue

            if await self._is_blacklisted_query.execute(guid):
                logger.info(
                    "Skipping blacklisted release for '%s' (attempt %s/%s)",
                    active.title,
                    index + 1,
                    len(torrent_results),
                )
                continue

            if excluded_hash and await self._is_same_removed_release(
                guid,
                torrent_result.magnetUrl,
                excluded_hash,
            ):
                logger.info(
                    "Skipping release with same infohash as removed torrent for '%s' "
                    "(attempt %s/%s, guid=%s...)",
                    active.title,
                    index + 1,
                    len(torrent_results),
                    guid[:48],
                )
                await self._blacklist_release(active, guid, reason=blacklist_reason)
                continue

            ok, _, _ = self._download_volume_space_checker.has_space_for_torrent(
                torrent_result.size
            )
            if not ok:
                await self._enqueue_deferred_use_case.execute(
                    entry=entry,
                    torrent_result=torrent_result,
                    search_query=search_query,
                    season=season,
                    episode=episode,
                    episode_name=episode_name,
                )
                logger.info(
                    "Deferred replacement torrent for '%s' — download volume full",
                    active.title,
                )
                return RetryActiveDownloadOutcome.DEFERRED

            new_torrent = await self._send_torrent_to_deluge_service.execute(
                torrent_result
            )
            if new_torrent is None:
                logger.warning(
                    "Replacement torrent send failed for '%s' (attempt %s/%s)",
                    active.title,
                    index + 1,
                    len(torrent_results),
                )
                continue

            sent_hash = normalize_infohash(new_torrent.hash)
            if excluded_hash and sent_hash == excluded_hash:
                logger.warning(
                    "Deluge re-added same infohash for '%s' via alternate Prowlarr guid; "
                    "blacklisting and trying next (hash=%s...)",
                    active.title,
                    sent_hash[:8],
                )
                await self._blacklist_release(active, guid, reason=blacklist_reason)
                await self._deluge_provider.remove_torrent(
                    new_torrent.hash, remove_data=True
                )
                continue

            updated = active.model_copy(
                update={
                    "prowlarr_guid": guid or active.prowlarr_guid,
                    "uid": new_torrent.hash,
                    "file_name": new_torrent.file_name,
                }
            )
            await self._update_active_download_use_case.execute(updated)
            logger.info(
                "Replacement torrent queued for '%s' (%s...)",
                active.title,
                new_torrent.hash[:8],
            )
            return RetryActiveDownloadOutcome.SUCCESS

        logger.error(
            "Failed to queue any replacement torrent for '%s' after %s result(s)",
            active.title,
            len(torrent_results),
        )
        return RetryActiveDownloadOutcome.SEND_FAILED

    async def _is_same_removed_release(
        self,
        guid: str,
        magnet_url: str | None,
        excluded_hash: str,
    ) -> bool:
        candidate = infohash_from_release(guid, magnet_url)
        return candidate == excluded_hash

    async def _blacklist_release(
        self,
        active: ActiveDownload,
        guid: str,
        *,
        reason: str,
    ) -> None:
        await self._add_torrent_to_blacklist.execute(
            guid,
            reason=reason,
            name=active.title,
            year=active.year,
            media_type=active.type,
        )

    async def _search_queries(
        self, active: ActiveDownload, *, media_type: str
    ) -> list[str]:
        if media_type == "tv":
            if active.season is None or active.episode is None:
                return [active.title]
            episode = TvEpisode(
                season=active.season,
                episode=active.episode,
                name=active.episode_name,
            )
            if self._watchlist_search_query_builder is not None:
                return self._watchlist_search_query_builder.build_tv_episode_search_queries(
                    watchlist_item_from_active_download(active).item,
                    episode,
                )
            if episode.name:
                return [
                    format_tv_episode_name_search_query(
                        active.title,
                        episode.season,
                        episode.episode,
                        episode.name,
                    ),
                    format_tv_episode_search_query(
                        active.title, episode.season, episode.episode
                    ),
                ]
            return [
                format_tv_episode_search_query(
                    active.title, episode.season, episode.episode
                )
            ]

        if active.year is not None:
            return [f"{active.title} {active.year}"]
        return [active.title]
