"""Remove unhealthy torrents, blacklist release, and re-add to watchlist."""
import logging

from app.application.blacklist_torrent.use_cases import AddTorrentToBlacklistUseCase
from app.application.pipelines.watchlist.use_cases.readd_watchlist_after_failure_use_case import (
    ReaddWatchlistAfterFailureUseCase,
)
from app.domain.models.active_download import ActiveDownload
from app.domain.models.torrent import Torrent
from app.domain.ports.external.deluge.deluge_provider import DelugeProvider
from app.domain.services.torrent_health import TorrentHealthThresholds, unhealthy_reason

logger = logging.getLogger(__name__)


class HandleUnhealthyTorrentUseCase:
    def __init__(
        self,
        deluge_provider: DelugeProvider,
        add_torrent_to_blacklist_use_case: AddTorrentToBlacklistUseCase,
        readd_watchlist_after_failure_use_case: ReaddWatchlistAfterFailureUseCase,
    ):
        self._deluge_provider = deluge_provider
        self._add_torrent_to_blacklist = add_torrent_to_blacklist_use_case
        self._readd_watchlist = readd_watchlist_after_failure_use_case

    async def execute(
        self,
        torrent: Torrent,
        active_download: ActiveDownload,
        *,
        thresholds: TorrentHealthThresholds,
    ) -> bool:
        reason = unhealthy_reason(torrent, thresholds=thresholds)
        if reason is None:
            return False

        logger.warning(
            "Removing unhealthy torrent '%s' (%s, reason=%s, progress=%.1f%%, "
            "availability=%s, last_seen_complete=%s, seeds=%s, peers=%s, "
            "tracker=%s, time_since_download=%s)",
            active_download.title,
            torrent.hash[:8],
            reason,
            float(torrent.progress or 0),
            torrent.availability,
            torrent.last_seen_complete,
            torrent.num_seeds,
            torrent.num_peers,
            torrent.tracker_status,
            torrent.time_since_download,
        )
        await self._add_torrent_to_blacklist.execute(
            active_download.prowlarr_guid,
            reason=f"unhealthy:{reason}",
            name=active_download.title,
            year=active_download.year,
            media_type=active_download.type,
        )
        await self._deluge_provider.remove_torrent(torrent.hash, remove_data=True)
        try:
            await self._readd_watchlist.execute(active_download)
        except Exception as exc:
            logger.error(
                "Failed to re-add '%s' to watchlist after unhealthy removal: %s",
                active_download.title,
                exc,
                exc_info=True,
            )
        return True
