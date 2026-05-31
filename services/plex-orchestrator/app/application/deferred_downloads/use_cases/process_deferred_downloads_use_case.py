"""Send pending deferred downloads to Prowlarr when download volume has enough space."""
from __future__ import annotations

import logging
from dataclasses import dataclass

from app.application.active_downloads.services.send_torrent_to_deluge_service import (
    SendTorrentToDelugeService,
)
from app.application.active_downloads.use_cases.create_active_download_use_case import (
    CreateActiveDownloadUseCase,
)
from app.domain.models.active_download import ActiveDownload
from app.domain.models.deferred_download import DeferredDownload
from app.domain.ports.repositories.deferred_downloads.deferred_download_repository_port import (
    DeferredDownloadRepositoryPort,
)
from app.domain.services.download_volume_space_checker import DownloadVolumeSpaceChecker
from app.domain.services.tv_episode_search_query import parse_season_episode

logger = logging.getLogger(__name__)


@dataclass
class ProcessDeferredDownloadsResult:
    checked: int = 0
    sent: int = 0
    still_pending: int = 0
    failed: int = 0


class ProcessDeferredDownloadsUseCase:
    def __init__(
        self,
        deferred_repo: DeferredDownloadRepositoryPort,
        space_checker: DownloadVolumeSpaceChecker,
        send_to_deluge: SendTorrentToDelugeService,
        create_active_download: CreateActiveDownloadUseCase,
    ):
        self._deferred_repo = deferred_repo
        self._space_checker = space_checker
        self._send_to_deluge = send_to_deluge
        self._create_active_download = create_active_download

    async def execute(self, *, limit: int = 20) -> ProcessDeferredDownloadsResult:
        pending = await self._deferred_repo.list_pending(limit=limit)
        result = ProcessDeferredDownloadsResult(checked=len(pending))

        for item in pending:
            ok, _, _ = self._space_checker.has_space_for_torrent(item.size_bytes)
            if not ok:
                result.still_pending += 1
                continue

            await self._deferred_repo.increment_attempt(item.id or 0)
            if await self._try_release(item):
                result.sent += 1
            else:
                result.failed += 1

        return result

    async def _try_release(self, item: DeferredDownload) -> bool:
        if not item.guid_prowlarr or not item.indexer_id:
            logger.error("Deferred item %s missing Prowlarr guid/indexer", item.id)
            return False

        torrent_result = item.to_torrent_search_result()
        new_torrent = await self._send_to_deluge.execute(
            torrent_result,
            time_added_threshold=5.0,
        )
        if new_torrent is None:
            logger.warning(
                "Deferred release failed: torrent not in Deluge (%s)",
                item.media_title,
            )
            return False

        season = item.season
        episode = item.episode
        if (season is None or episode is None) and item.search_query:
            parsed = parse_season_episode(item.search_query)
            if parsed:
                season = season if season is not None else parsed.season
                episode = episode if episode is not None else parsed.episode

        await self._create_active_download.execute(
            ActiveDownload(
                plex_guid=item.guid_plex,
                plex_library_guid=item.plex_library_guid,
                watchlist_item_id=item.rating_key,
                plex_user_token=item.plex_user_token,
                watchlist_source=item.watchlist_source,
                tmdb_media_id=item.tmdb_media_id,
                tmdb_account_id=item.tmdb_account_id,
                prowlarr_guid=item.guid_prowlarr,
                uid=new_torrent.hash,
                title=item.media_title,
                file_name=new_torrent.file_name,
                year=item.year,
                type=item.media_type,
                season=season,
                episode=episode,
                episode_name=item.episode_name,
            )
        )
        if item.id:
            await self._deferred_repo.mark_sent(item.id)
        logger.info("Released deferred torrent for '%s'", item.media_title)
        return True
