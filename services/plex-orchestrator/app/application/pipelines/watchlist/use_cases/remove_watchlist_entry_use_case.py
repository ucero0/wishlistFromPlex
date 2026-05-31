"""Remove a watchlist item from Plex or TMDB depending on source."""
import logging

from app.application.plex.use_cases.remove_watchlist_item_use_case import (
    RemoveWatchlistItemUseCase,
)
from app.application.tmdb.use_cases.remove_tmdb_watchlist_item_use_case import (
    RemoveTmdbWatchlistItemUseCase,
)
from app.domain.models.active_download import ActiveDownload
from app.domain.models.deferred_download import DeferredDownload
from app.domain.models.watchlist_item_for_user import WatchlistItemForUser
from app.domain.models.watchlist_source import WatchlistSource
from app.domain.ports.external.tmdb.tmdb_watchlist_provider import TmdbWatchlistProvider
from app.domain.services.tmdb_guid import parse_tmdb_guid

logger = logging.getLogger(__name__)

_IDENTITY_QUEUE_REASONS = frozenset(
    {
        "same_media_identity_downloading",
        "same_media_identity_deferred",
    }
)


class RemoveWatchlistEntryUseCase:
    def __init__(
        self,
        remove_plex_watchlist_item_use_case: RemoveWatchlistItemUseCase,
        remove_tmdb_watchlist_item_use_case: RemoveTmdbWatchlistItemUseCase,
        tmdb_watchlist_provider: TmdbWatchlistProvider,
    ):
        self._remove_plex = remove_plex_watchlist_item_use_case
        self._remove_tmdb = remove_tmdb_watchlist_item_use_case
        self._tmdb_watchlist_provider = tmdb_watchlist_provider

    @staticmethod
    def should_remove_when_already_queued(queue_reason: str | None) -> bool:
        """Do not remove another platform's watchlist when only title/year matched."""
        return queue_reason not in _IDENTITY_QUEUE_REASONS

    async def execute(self, entry: WatchlistItemForUser) -> None:
        if entry.source == WatchlistSource.TMDB:
            media_id = self._tmdb_media_id_from_entry(entry)
            if (
                media_id is None
                or entry.tmdb_account_id is None
                or not entry.tmdb_access_token
            ):
                return
            media_type = self._media_type_from_item(entry)
            await self._remove_tmdb.execute(
                entry.tmdb_account_id,
                entry.tmdb_access_token,
                media_type,
                media_id,
            )
            logger.info(
                "Removed TMDB watchlist item %s (%s/%s) for account %s",
                entry.item.title,
                media_type,
                media_id,
                entry.tmdb_account_id,
            )
            return

        if entry.item.rating_key and entry.plex_user_token:
            await self._remove_plex.execute(
                entry.item.rating_key, entry.plex_user_token
            )
            logger.info(
                "Removed Plex watchlist item %s (guid=%s, ratingKey=%s)",
                entry.item.title,
                entry.item.guid,
                entry.item.rating_key,
            )

    async def execute_from_active_download(self, download: ActiveDownload) -> None:
        source = (download.watchlist_source or "").lower()
        if source == WatchlistSource.TMDB.value:
            await self._remove_tmdb_download(download)
            return
        if source == WatchlistSource.PLEX.value or download.watchlist_item_id:
            await self._remove_plex_download(download)
            return
        parsed = parse_tmdb_guid(download.plex_guid)
        if parsed:
            await self._remove_tmdb_download(download, parsed=parsed)
            return
        await self._remove_plex_download(download)

    async def execute_from_deferred(self, item: DeferredDownload) -> None:
        download = ActiveDownload(
            plex_guid=item.guid_plex,
            plex_library_guid=item.plex_library_guid,
            watchlist_item_id=item.rating_key,
            plex_user_token=item.plex_user_token,
            watchlist_source=item.watchlist_source,
            tmdb_media_id=item.tmdb_media_id,
            tmdb_account_id=item.tmdb_account_id,
            prowlarr_guid=item.guid_prowlarr,
            uid="",
            title=item.media_title,
            type=item.media_type,
            year=item.year,
        )
        await self.execute_from_active_download(download)

    async def _remove_tmdb_download(
        self,
        download: ActiveDownload,
        *,
        parsed: tuple[str, int] | None = None,
    ) -> None:
        if not download.plex_user_token:
            return
        media_id = download.tmdb_media_id
        if media_id is None and parsed:
            media_id = parsed[1]
        if media_id is None:
            parsed_guid = parse_tmdb_guid(download.plex_guid)
            if parsed_guid:
                media_id = parsed_guid[1]
        if media_id is None:
            return
        account_id = download.tmdb_account_id
        if account_id is None:
            account_id = await self._tmdb_watchlist_provider.get_account_id(
                download.plex_user_token
            )
        media_type = "tv" if download.type in ("show", "tvshow") else "movie"
        await self._remove_tmdb.execute(
            account_id,
            download.plex_user_token,
            media_type,
            media_id,
        )
        logger.info(
            "Removed TMDB watchlist item %s (%s/%s) after download finished",
            download.title,
            media_type,
            media_id,
        )

    async def _remove_plex_download(self, download: ActiveDownload) -> None:
        if not download.watchlist_item_id or not download.plex_user_token:
            logger.warning(
                "Cannot remove Plex watchlist for %s: missing ratingKey or token (guid=%s)",
                download.title,
                download.plex_guid,
            )
            return
        await self._remove_plex.execute(
            download.watchlist_item_id, download.plex_user_token
        )
        logger.info(
            "Removed Plex watchlist item %s (guid=%s, ratingKey=%s) after download finished",
            download.title,
            download.plex_guid,
            download.watchlist_item_id,
        )

    @staticmethod
    def _tmdb_media_id_from_entry(entry: WatchlistItemForUser) -> int | None:
        if entry.item.rating_key and entry.item.rating_key.isdigit():
            return int(entry.item.rating_key)
        parsed = parse_tmdb_guid(entry.item.guid or "")
        return parsed[1] if parsed else None

    @staticmethod
    def _media_type_from_item(entry: WatchlistItemForUser) -> str:
        media_type = entry.item.type
        value = media_type.value if hasattr(media_type, "value") else str(media_type)
        return "tv" if value in ("show", "tvshow") else "movie"
