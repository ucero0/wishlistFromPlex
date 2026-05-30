"""Composition root for Plex watchlist and server external integration."""
from app.adapters.external.plex_client.adapter import PlexWatchlistAdapter
from app.adapters.external.plex_server.adapter import PlexServerLibraryAdapter
from app.application.plex.queries.get_plex_library_locations_query import (
    GetPlexLibraryLocationsByMediaQuery,
)
from app.application.plex.queries.get_plex_server_item_query import IsItemInLibraryQuery
from app.application.plex.queries.get_watchlist_query import GetWatchlistQuery
from app.application.plex.queries.test_plex_server_connection_query import TestPlexServerConnectionQuery
from app.application.plex.queries.test_plex_server_admin_token_query import (
    TestPlexServerAdminTokenQuery,
)
from app.application.plex.use_cases.add_watchlist_item_use_case import AddWatchlistItemUseCase
from app.application.plex.use_cases.partial_scan_library_use_case import PartialScanLibraryUseCase
from app.application.plex.use_cases.remove_watchlist_item_use_case import RemoveWatchlistItemUseCase
from app.infrastructure.external_apis.plex.plex_client.client import PlexWatchlistClient
from app.infrastructure.external_apis.plex.plex_server.client import PlexServerLibraryApiClient


def build_plex_watchlist_adapter() -> PlexWatchlistAdapter:
    return PlexWatchlistAdapter(PlexWatchlistClient())


def build_plex_server_adapter() -> PlexServerLibraryAdapter:
    return PlexServerLibraryAdapter(PlexServerLibraryApiClient())


def build_get_watchlist_query() -> GetWatchlistQuery:
    return GetWatchlistQuery(build_plex_watchlist_adapter())


def build_remove_watchlist_item_use_case() -> RemoveWatchlistItemUseCase:
    return RemoveWatchlistItemUseCase(build_plex_watchlist_adapter())


def build_add_watchlist_item_use_case() -> AddWatchlistItemUseCase:
    return AddWatchlistItemUseCase(build_plex_watchlist_adapter())


def build_test_plex_server_connection_query() -> TestPlexServerConnectionQuery:
    return TestPlexServerConnectionQuery(build_plex_server_adapter())


def build_test_plex_server_admin_token_query() -> TestPlexServerAdminTokenQuery:
    return TestPlexServerAdminTokenQuery(build_plex_server_adapter())


def build_is_item_in_library_query() -> IsItemInLibraryQuery:
    return IsItemInLibraryQuery(build_plex_server_adapter())


def build_get_plex_library_locations_by_media_query() -> GetPlexLibraryLocationsByMediaQuery:
    return GetPlexLibraryLocationsByMediaQuery(build_plex_server_adapter())


def build_partial_scan_library_use_case() -> PartialScanLibraryUseCase:
    return PartialScanLibraryUseCase(build_plex_server_adapter())
