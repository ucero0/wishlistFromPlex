"""Re-add watchlist items on Plex or TMDB after a failed ingest."""
import logging

from app.application.plex.use_cases.add_watchlist_item_use_case import AddWatchlistItemUseCase
from app.application.tmdb.use_cases.add_tmdb_watchlist_item_use_case import (
    AddTmdbWatchlistItemUseCase,
)
from app.domain.models.active_download import ActiveDownload
from app.domain.models.watchlist_source import WatchlistSource
from app.domain.services.tmdb_guid import parse_tmdb_guid

logger = logging.getLogger(__name__)


class ReaddWatchlistAfterFailureUseCase:
    def __init__(
        self,
        add_plex_watchlist_item_use_case: AddWatchlistItemUseCase,
        add_tmdb_watchlist_item_use_case: AddTmdbWatchlistItemUseCase,
    ):
        self._add_plex = add_plex_watchlist_item_use_case
        self._add_tmdb = add_tmdb_watchlist_item_use_case

    async def execute(self, torrent_download: ActiveDownload) -> None:
        source = (torrent_download.watchlist_source or "").lower()
        if source == WatchlistSource.TMDB.value:
            await self._readd_tmdb(torrent_download)
            return
        if source == WatchlistSource.PLEX.value or torrent_download.watchlist_item_id:
            await self._readd_plex(torrent_download)
            return
        if parse_tmdb_guid(torrent_download.plex_guid):
            await self._readd_tmdb(torrent_download)
            return
        await self._readd_plex(torrent_download)

    async def _readd_plex(self, torrent_download: ActiveDownload) -> None:
        if not torrent_download.watchlist_item_id:
            logger.warning(
                "RatingKey not available for %s (guid=%s). Cannot add back to Plex watchlist.",
                torrent_download.title,
                torrent_download.plex_guid,
            )
            return
        if not torrent_download.plex_user_token:
            logger.warning(
                "Plex user token not available for %s (guid=%s). Cannot add back to Plex watchlist.",
                torrent_download.title,
                torrent_download.plex_guid,
            )
            return
        await self._add_plex.execute(
            torrent_download.watchlist_item_id,
            torrent_download.plex_user_token,
        )
        logger.info("Added %s back to Plex watchlist", torrent_download.title)

    async def _readd_tmdb(self, torrent_download: ActiveDownload) -> None:
        media_id = torrent_download.tmdb_media_id
        if media_id is None:
            parsed = parse_tmdb_guid(torrent_download.plex_guid)
            if parsed:
                media_id = parsed[1]
        if media_id is None or not torrent_download.plex_user_token:
            logger.warning(
                "TMDB ids not available for %s. Cannot add back to TMDB watchlist.",
                torrent_download.title,
            )
            return
        account_id = torrent_download.tmdb_account_id
        if account_id is None:
            logger.warning(
                "TMDB account id not available for %s. Cannot add back to TMDB watchlist.",
                torrent_download.title,
            )
            return
        media_type = "tv" if torrent_download.type in ("show", "tvshow") else "movie"
        await self._add_tmdb.execute(
            account_id,
            torrent_download.plex_user_token,
            media_type,
            media_id,
        )
        logger.info("Added %s back to TMDB watchlist", torrent_download.title)
