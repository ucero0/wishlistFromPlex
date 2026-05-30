"""Composition root for watchlist download pipeline."""
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.pipelines.watchlist.queries.should_skip_watchlist_item_query import (
    ShouldSkipWatchlistItemQuery,
)
from app.application.pipelines.watchlist.services.watchlist_search_builder import (
    WatchlistSearchQueryBuilder,
)
from app.application.pipelines.watchlist.use_cases.process_plex_watchlist_downloads_use_case import (
    ProcessPlexWatchlistDownloadsUseCase,
)
from app.application.pipelines.watchlist.use_cases.process_watchlist_item_use_case import (
    ProcessWatchlistItemUseCase,
)
from app.application.pipelines.watchlist.use_cases.try_send_torrent_for_watchlist_item_use_case import (
    TrySendTorrentForWatchlistItemUseCase,
)
from app.composition.blacklist_torrent import build_is_blacklisted_by_guid_prowlarr_query
from app.composition.deferred_downloads import (
    build_enqueue_deferred_download_use_case,
    build_process_deferred_downloads_use_case,
    build_send_torrent_to_deluge_service,
)
from app.composition.infrastructure_services import build_download_volume_space_checker
from app.composition.media_queue import build_is_media_already_queued_query
from app.composition.plex_users import build_get_plex_user_query
from app.composition.active_downloads import (
    build_create_active_download_use_case,
    build_reconcile_active_downloads_with_deluge_use_case,
)
from app.composition.plex_external import (
    build_get_watchlist_query,
    build_is_item_in_library_query,
    build_remove_watchlist_item_use_case,
)
from app.composition.prowlarr import build_find_best_torrent_query
from app.composition.tmdb import build_get_original_title_from_tmdb_query


def build_try_send_torrent_for_watchlist_item_use_case(
    session: AsyncSession,
) -> TrySendTorrentForWatchlistItemUseCase:
    return TrySendTorrentForWatchlistItemUseCase(
        is_blacklisted_query=build_is_blacklisted_by_guid_prowlarr_query(session),
        is_media_already_queued_query=build_is_media_already_queued_query(session),
        remove_watchlist_item_use_case=build_remove_watchlist_item_use_case(),
        download_volume_space_checker=build_download_volume_space_checker(),
        enqueue_deferred_use_case=build_enqueue_deferred_download_use_case(
            session
        ),
        send_torrent_to_deluge_service=build_send_torrent_to_deluge_service(),
    )


def build_process_watchlist_item_use_case(
    session: AsyncSession,
) -> ProcessWatchlistItemUseCase:
    return ProcessWatchlistItemUseCase(
        watchlist_search_query_builder=WatchlistSearchQueryBuilder(
            build_get_original_title_from_tmdb_query()
        ),
        find_best_torrent_query=build_find_best_torrent_query(),
        try_send_torrent_use_case=build_try_send_torrent_for_watchlist_item_use_case(
            session
        ),
        create_active_download_use_case=build_create_active_download_use_case(session),
        remove_watchlist_item_use_case=build_remove_watchlist_item_use_case(),
    )


def build_should_skip_watchlist_item_query(
    session: AsyncSession,
) -> ShouldSkipWatchlistItemQuery:
    return ShouldSkipWatchlistItemQuery(
        is_item_in_library_query=build_is_item_in_library_query(),
        is_media_already_queued_query=build_is_media_already_queued_query(session),
        remove_watchlist_item_use_case=build_remove_watchlist_item_use_case(),
    )


def build_process_plex_watchlist_downloads_use_case(
    session: AsyncSession,
) -> ProcessPlexWatchlistDownloadsUseCase:
    return ProcessPlexWatchlistDownloadsUseCase(
        get_plex_user_query=build_get_plex_user_query(session),
        get_watchlist_query=build_get_watchlist_query(),
        reconcile_active_downloads_use_case=build_reconcile_active_downloads_with_deluge_use_case(
            session
        ),
        process_deferred_downloads_use_case=build_process_deferred_downloads_use_case(
            session
        ),
        should_skip_watchlist_item_query=build_should_skip_watchlist_item_query(session),
        process_watchlist_item_use_case=build_process_watchlist_item_use_case(session),
    )
