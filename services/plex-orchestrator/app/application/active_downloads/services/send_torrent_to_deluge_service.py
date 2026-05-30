"""Send a Prowlarr release to Deluge and confirm it appears in the client."""
from __future__ import annotations

import asyncio
import logging
from typing import Optional

from app.application.deluge.queries.get_torrent_status_query import GetTorrentByNameQuery
from app.application.prowlarr.use_cases.download_torrent_use_case import DownloadTorrentUseCase
from app.domain.models.torrent import Torrent
from app.domain.models.torrent_search import TorrentSearchResult

logger = logging.getLogger(__name__)


class SendTorrentToDelugeService:
    def __init__(
        self,
        download_torrent: DownloadTorrentUseCase,
        get_torrent_by_name: GetTorrentByNameQuery,
    ):
        self._download_torrent = download_torrent
        self._get_torrent_by_name = get_torrent_by_name

    async def execute(
        self,
        torrent_result: TorrentSearchResult,
        *,
        time_added_threshold: float = 3.0,
        settle_seconds: float = 2.0,
    ) -> Optional[Torrent]:
        await self._download_torrent.execute(torrent_result)
        await asyncio.sleep(settle_seconds)
        torrent = await self._get_torrent_by_name.execute(
            torrent_result.title,
            time_added_threshold=time_added_threshold,
        )
        if torrent is None and time_added_threshold is not None:
            torrent = await self._get_torrent_by_name.execute(
                torrent_result.title,
                time_added_threshold=None,
            )
        if torrent is None:
            logger.warning(
                "Torrent not found in Deluge after send: %s",
                torrent_result.title,
            )
        return torrent
