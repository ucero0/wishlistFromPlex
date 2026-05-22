"""Send pending deferred torrents to Prowlarr when download volume has enough space."""
from __future__ import annotations

import logging
from dataclasses import dataclass

from app.application.plex.useCases.removeWatchListItem import RemoveWatchListItemUseCase
from app.application.torrentDownload.services.sendTorrentToDeluge import (
    SendTorrentToDelugeService,
)
from app.application.torrentDownload.useCases.createTorrentDownload import (
    CreateTorrentDownloadUseCase,
)
from app.domain.models.deferred_torrent_download import DeferredTorrentDownload
from app.domain.models.torrentDownload import TorrentDownload
from app.domain.ports.repositories.deferredTorrent.deferredTorrentRepo import (
    DeferredTorrentRepoPort,
)
from app.domain.services.download_volume_space_checker import DownloadVolumeSpaceChecker

logger = logging.getLogger(__name__)


@dataclass
class ProcessDeferredTorrentDownloadsResult:
    checked: int = 0
    sent: int = 0
    still_pending: int = 0
    failed: int = 0


class ProcessDeferredTorrentDownloadsUseCase:
    def __init__(
        self,
        deferred_repo: DeferredTorrentRepoPort,
        space_checker: DownloadVolumeSpaceChecker,
        send_to_deluge: SendTorrentToDelugeService,
        create_torrent_download: CreateTorrentDownloadUseCase,
        remove_watchlist_item: RemoveWatchListItemUseCase,
    ):
        self._deferred_repo = deferred_repo
        self._space_checker = space_checker
        self._send_to_deluge = send_to_deluge
        self._create_torrent_download = create_torrent_download
        self._remove_watchlist = remove_watchlist_item

    async def execute(self, *, limit: int = 20) -> ProcessDeferredTorrentDownloadsResult:
        pending = await self._deferred_repo.list_pending(limit=limit)
        result = ProcessDeferredTorrentDownloadsResult(checked=len(pending))

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

    async def _try_release(self, item: DeferredTorrentDownload) -> bool:
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

        await self._create_torrent_download.execute(
            TorrentDownload(
                plex_guid=item.guid_plex,
                watchlist_item_id=item.rating_key,
                plex_user_token=item.plex_user_token,
                prowlarr_guid=item.guid_prowlarr,
                uid=new_torrent.hash,
                title=item.media_title,
                file_name=new_torrent.file_name,
                year=item.year,
                type=item.media_type,
            )
        )
        if item.id:
            await self._deferred_repo.mark_sent(item.id)
        if item.rating_key and item.plex_user_token:
            await self._remove_watchlist.execute(
                item.rating_key, item.plex_user_token
            )
        logger.info("Released deferred torrent for '%s'", item.media_title)
        return True
