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
from app.application.pipelines.watchlist.services.watchlist_search_builder import (
    is_show_watchlist,
)
from app.domain.models.watchlist_subscriber import WatchlistSubscriber
from app.domain.ports.external.tmdb.tmdb_watchlist_provider import TmdbWatchlistProvider
from app.domain.services.tmdb_guid import parse_tmdb_guid
from app.domain.services.watchlist_download_tracking import tmdb_media_id_from_item

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

    async def execute(
        self, entry: WatchlistItemForUser, *, removal_reason: str | None = None
    ) -> None:
        if is_show_watchlist(entry.item) and removal_reason != "show_complete":
            logger.info(
                "Not removing show '%s' from watchlist (reason=%s); "
                "shows are only cleared when every catalog episode is owned in Plex",
                entry.item.title,
                removal_reason,
            )
            return

        media_type = self._media_type_from_item(entry)
        for subscriber in entry.all_subscribers():
            await self._remove_subscriber(
                entry.item.title or "",
                media_type,
                subscriber,
            )

    async def _remove_subscriber(
        self,
        title: str,
        media_type: str,
        subscriber: WatchlistSubscriber,
    ) -> None:
        if subscriber.source == WatchlistSource.TMDB:
            media_id = subscriber.tmdb_media_id
            if media_id is None:
                return
            if subscriber.tmdb_account_id is None or not subscriber.tmdb_access_token:
                return
            await self._remove_tmdb.execute(
                subscriber.tmdb_account_id,
                subscriber.tmdb_access_token,
                media_type,
                media_id,
            )
            logger.info(
                "Removed TMDB watchlist item %s (%s/%s) for account %s",
                title,
                media_type,
                media_id,
                subscriber.tmdb_account_id,
            )
            return

        rating_key = subscriber.plex_watchlist_rating_key
        if rating_key and subscriber.plex_user_token:
            await self._remove_plex.execute(rating_key, subscriber.plex_user_token)
            logger.info(
                "Removed Plex watchlist item %s (ratingKey=%s)",
                title,
                rating_key,
            )

    async def execute_from_active_download(self, download: ActiveDownload) -> None:
        if download.watchlist_subscribers:
            media_type = "tv" if download.type in ("show", "tvshow") else "movie"
            for subscriber in download.watchlist_subscribers:
                await self._remove_subscriber(
                    download.title,
                    media_type,
                    subscriber,
                )
            return

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
            watchlist_subscribers=item.watchlist_subscribers,
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
        return tmdb_media_id_from_item(entry)

    @staticmethod
    def _media_type_from_item(entry: WatchlistItemForUser) -> str:
        media_type = entry.item.type
        value = media_type.value if hasattr(media_type, "value") else str(media_type)
        return "tv" if value in ("show", "tvshow") else "movie"
