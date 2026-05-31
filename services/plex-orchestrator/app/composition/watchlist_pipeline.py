"""Composition root for watchlist download pipeline."""
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.pipelines.watchlist.queries.get_missing_tv_episodes_query import (
    GetMissingTvEpisodesQuery,
)
from app.application.pipelines.watchlist.queries.is_episode_already_queued_query import (
    IsEpisodeAlreadyQueuedQuery,
)
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
from app.composition.tmdb_users import build_get_tmdb_user_query
from app.composition.active_downloads import (
    build_create_active_download_use_case,
    build_reconcile_active_downloads_with_deluge_use_case,
)
from app.composition.persistence import (
    build_active_download_repository,
    build_deferred_download_repository,
)
from app.composition.plex_external import (
    build_get_watchlist_query,
    build_is_item_in_library_query,
    build_plex_watchlist_adapter,
    build_plex_server_adapter,
)
from app.application.plex.queries.enrich_watchlist_with_plex_identity_query import (
    EnrichWatchlistWithPlexIdentityQuery,
)
from app.application.plex.queries.resolve_plex_library_identity_query import (
    ResolvePlexLibraryIdentityQuery,
)
from app.application.plex.queries.get_latest_watched_episode_for_show_query import (
    GetLatestWatchedEpisodeForShowQuery,
)
from app.application.plex.queries.get_plex_discover_show_catalog_episodes_query import (
    GetPlexDiscoverShowCatalogEpisodesQuery,
)
from app.application.plex.queries.get_plex_server_show_catalog_episodes_query import (
    GetPlexServerShowCatalogEpisodesQuery,
)
from app.application.plex.queries.get_owned_show_episodes_query import (
    GetOwnedShowEpisodesQuery,
)
from app.application.plex.queries.get_show_catalog_episodes_query import (
    GetShowCatalogEpisodesQuery,
)
from app.composition.prowlarr import build_find_best_torrent_query
from app.composition.tmdb import (
    build_get_original_title_from_tmdb_query,
    build_get_tmdb_show_catalog_episodes_query,
    build_get_tmdb_watchlist_query,
    build_remove_watchlist_entry_use_case,
    build_resolve_tmdb_tv_id_for_show_query,
)


def build_enrich_watchlist_with_plex_identity_query() -> EnrichWatchlistWithPlexIdentityQuery:
    return EnrichWatchlistWithPlexIdentityQuery(
        ResolvePlexLibraryIdentityQuery(build_plex_server_adapter())
    )


def build_is_episode_already_queued_query(
    session: AsyncSession,
) -> IsEpisodeAlreadyQueuedQuery:
    return IsEpisodeAlreadyQueuedQuery(
        torrent_repo=build_active_download_repository(session),
        deferred_repo=build_deferred_download_repository(session),
    )


def build_get_missing_tv_episodes_query(
    session: AsyncSession,
) -> GetMissingTvEpisodesQuery:
    library_adapter = build_plex_server_adapter()
    return GetMissingTvEpisodesQuery(
        get_catalog_episodes_query=GetShowCatalogEpisodesQuery(
            GetPlexDiscoverShowCatalogEpisodesQuery(build_plex_watchlist_adapter()),
            GetPlexServerShowCatalogEpisodesQuery(library_adapter),
            build_resolve_tmdb_tv_id_for_show_query(),
            build_get_tmdb_show_catalog_episodes_query(),
        ),
        get_owned_episodes_query=GetOwnedShowEpisodesQuery(library_adapter),
        is_episode_already_queued_query=build_is_episode_already_queued_query(session),
        get_latest_watched_episode_query=GetLatestWatchedEpisodeForShowQuery(
            library_adapter,
            build_get_plex_user_query(session),
        ),
    )


def build_try_send_torrent_for_watchlist_item_use_case(
    session: AsyncSession,
) -> TrySendTorrentForWatchlistItemUseCase:
    return TrySendTorrentForWatchlistItemUseCase(
        is_blacklisted_query=build_is_blacklisted_by_guid_prowlarr_query(session),
        is_media_already_queued_query=build_is_media_already_queued_query(session),
        is_episode_already_queued_query=build_is_episode_already_queued_query(session),
        remove_watchlist_entry_use_case=build_remove_watchlist_entry_use_case(session),
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
        remove_watchlist_entry_use_case=build_remove_watchlist_entry_use_case(session),
        get_missing_tv_episodes_query=build_get_missing_tv_episodes_query(session),
    )


def build_should_skip_watchlist_item_query(
    session: AsyncSession,
) -> ShouldSkipWatchlistItemQuery:
    return ShouldSkipWatchlistItemQuery(
        is_item_in_library_query=build_is_item_in_library_query(),
        is_media_already_queued_query=build_is_media_already_queued_query(session),
        remove_watchlist_entry_use_case=build_remove_watchlist_entry_use_case(session),
        get_missing_tv_episodes_query=build_get_missing_tv_episodes_query(session),
    )


def build_process_plex_watchlist_downloads_use_case(
    session: AsyncSession,
) -> ProcessPlexWatchlistDownloadsUseCase:
    return ProcessPlexWatchlistDownloadsUseCase(
        get_plex_user_query=build_get_plex_user_query(session),
        get_watchlist_query=build_get_watchlist_query(),
        get_tmdb_user_query=build_get_tmdb_user_query(session),
        get_tmdb_watchlist_query=build_get_tmdb_watchlist_query(),
        reconcile_active_downloads_use_case=build_reconcile_active_downloads_with_deluge_use_case(
            session
        ),
        process_deferred_downloads_use_case=build_process_deferred_downloads_use_case(
            session
        ),
        enrich_watchlist_with_plex_identity_query=build_enrich_watchlist_with_plex_identity_query(),
        should_skip_watchlist_item_query=build_should_skip_watchlist_item_query(session),
        process_watchlist_item_use_case=build_process_watchlist_item_use_case(session),
    )
