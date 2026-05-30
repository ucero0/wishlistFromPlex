"""Ensure infrastructure repositories implement their port contracts."""
from app.infrastructure.persistence.antivirus.repo.antivirus_repository import (
    AntivirusRepository,
)
from app.infrastructure.persistence.blacklist_torrent.repo.blacklist_torrent_repository import (
    BlacklistActiveDownloadRepository,
)
from app.infrastructure.persistence.deferred_downloads.repo.deferred_download_repository import (
    DeferredDownloadRepository,
)
from app.infrastructure.persistence.plex.repo.plex_library_path_repository import (
    PlexLibraryPathRepository,
)
from app.infrastructure.persistence.plex.repo.plex_user_repository import PlexUserRepository
from app.infrastructure.persistence.active_downloads.repo.active_download_repository import (
    ActiveDownloadRepository,
)


def _assert_methods(repo_cls: type, method_names: list[str]) -> None:
    for method_name in method_names:
        assert hasattr(repo_cls, method_name), (
            f"{repo_cls.__name__} missing method: {method_name}"
        )


def test_torrent_repository_contract() -> None:
    _assert_methods(
        ActiveDownloadRepository,
        [
            "get_by_id",
            "get_by_uid",
            "get_by_guid_plex",
            "is_guid_plex_downloading",
            "get_by_guid_prowlarr",
            "has_by_media_identity",
            "get_by_type",
            "get_all",
            "create",
            "update",
            "delete",
            "delete_by_id",
        ],
    )


def test_antivirus_repository_contract() -> None:
    _assert_methods(
        AntivirusRepository,
        [
            "get_by_id",
            "get_by_guid_prowlarr",
            "get_clean_pending_ingest_by_guid_prowlarr",
            "has_infected_by_guid_prowlarr",
            "get_by_file_path",
            "get_infected_items",
            "get_clean_items",
            "get_all",
            "create",
            "update",
            "delete",
            "delete_by_id",
            "delete_by_guid_prowlarr",
        ],
    )


def test_blacklist_torrent_repository_contract() -> None:
    _assert_methods(
        BlacklistActiveDownloadRepository,
        ["is_blacklisted", "add", "get_all", "get_by_guid", "delete_by_guid"],
    )


def test_deferred_download_repository_contract() -> None:
    _assert_methods(
        DeferredDownloadRepository,
        [
            "get_pending_by_guid_plex",
            "get_pending_by_guid_prowlarr",
            "get_pending_by_media_identity",
            "list_pending",
            "upsert_pending",
            "mark_sent",
            "increment_attempt",
            "update",
        ],
    )


def test_plex_user_repository_contract() -> None:
    _assert_methods(
        PlexUserRepository,
        [
            "get_active_users",
            "get_user_by_id",
            "get_user_by_name",
            "get_user_by_plex_token",
            "create_user",
            "update_user",
            "delete_user",
        ],
    )


def test_plex_library_path_repository_contract() -> None:
    _assert_methods(
        PlexLibraryPathRepository,
        ["list_active_by_media_type", "list_all", "sync_from_server", "apply_disk_stats"],
    )
