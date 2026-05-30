from app.application.plex.queries.get_plex_library_locations_query import (
    GetPlexLibraryLocationsByMediaQuery,
)
from app.application.plex.queries.get_plex_server_item_query import IsItemInLibraryQuery
from app.application.plex.queries.test_plex_server_admin_token_query import (
    TestPlexServerAdminTokenQuery,
)
from app.application.plex.queries.test_plex_server_connection_query import TestPlexServerConnectionQuery
from app.application.plex.use_cases.partial_scan_library_use_case import PartialScanLibraryUseCase
from app.composition.plex_external import (
    build_get_plex_library_locations_by_media_query,
    build_is_item_in_library_query,
    build_partial_scan_library_use_case,
    build_test_plex_server_admin_token_query,
    build_test_plex_server_connection_query,
)


def create_test_plex_server_connection_query() -> TestPlexServerConnectionQuery:
    return build_test_plex_server_connection_query()


def create_test_plex_server_admin_token_query() -> TestPlexServerAdminTokenQuery:
    return build_test_plex_server_admin_token_query()


def create_is_item_in_library_query() -> IsItemInLibraryQuery:
    return build_is_item_in_library_query()


def create_get_plex_library_locations_by_media_query() -> GetPlexLibraryLocationsByMediaQuery:
    return build_get_plex_library_locations_by_media_query()


def create_partial_scan_library_use_case() -> PartialScanLibraryUseCase:
    return build_partial_scan_library_use_case()
