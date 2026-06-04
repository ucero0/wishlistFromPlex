"""Tests for clean-torrent ingest (copy to library, Deluge remove with data)."""
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.pipelines.ingest.use_cases.ingest_clean_torrent_use_case import (
    IngestCleanTorrentUseCase,
)
from app.domain.models.active_download import ActiveDownload
from app.domain.models.antivirus_scan import AntivirusScan
from app.domain.models.media_integrity_result import MediaIntegrityResult


def _movie_download() -> ActiveDownload:
    return ActiveDownload(
        plex_guid="plex-movie-1",
        prowlarr_guid="guid-movie-1",
        uid="a" * 40,
        title="Test Movie",
        file_name="Test Movie (2024)",
        type="movie",
        year=2024,
    )


def _scan_record() -> AntivirusScan:
    return AntivirusScan(
        id=1,
        prowlarr_guid="guid-movie-1",
        source_folder_path="/quarantine/Test Movie (2024)",
        is_infected=False,
        scanned_at=datetime.now(),
    )


def _build_use_case(*, copy_result: bool = True) -> tuple[IngestCleanTorrentUseCase, MagicMock]:
    filesystem = MagicMock()
    filesystem.list_video_files.return_value = []
    filesystem.copy.return_value = copy_result
    filesystem.explain_copy_failure.return_value = "copy failed"
    deluge = AsyncMock()
    deluge.remove_torrent = AsyncMock(return_value=True)
    destination_selector = AsyncMock()
    destination_selector.select = AsyncMock(return_value=MagicMock(path="/plex/movies", section_id=1))
    destination_resolver = MagicMock()
    destination_resolver.resolve.return_value = "/plex/movies/Test Movie (2024)/Test Movie (2024).mkv"
    destination_resolver.folder_path_for_plex_scan.return_value = "/plex/movies/Test Movie (2024)"
    partial_scan = AsyncMock()
    sync_paths = AsyncMock()
    refresh_disk = AsyncMock()
    reconcile = AsyncMock()
    reconcile.execute = AsyncMock(return_value={"removed_count": 1, "updated_count": 0, "total_checked": 1})
    remove_watchlist = AsyncMock()
    antivirus_repo = AsyncMock()
    antivirus_repo.update = AsyncMock()
    verify = MagicMock()
    verify.execute.return_value = MediaIntegrityResult(
        is_valid=True,
        checked_files=["/quarantine/Test Movie (2024)/movie.mkv"],
    )
    handle_corrupt = AsyncMock()

    use_case = IngestCleanTorrentUseCase(
        filesystem_service=filesystem,
        antivirus_repo=antivirus_repo,
        deluge_provider=deluge,
        destination_selector=destination_selector,
        destination_resolver=destination_resolver,
        partial_scan_library_use_case=partial_scan,
        sync_library_paths_use_case=sync_paths,
        refresh_disk_stats_use_case=refresh_disk,
        reconcile_active_downloads_use_case=reconcile,
        remove_watchlist_entry_use_case=remove_watchlist,
        verify_media_integrity_use_case=verify,
        handle_corrupt_media_use_case=handle_corrupt,
    )
    return use_case, deluge


@pytest.mark.asyncio
async def test_ingest_copies_to_library_and_removes_torrent_with_data():
    use_case, deluge = _build_use_case(copy_result=True)
    scan = _scan_record()

    result = await use_case.execute(
        "a" * 40,
        _movie_download(),
        scan,
        "/quarantine/Test Movie (2024)",
        is_file=False,
        scanned_files=["/quarantine/Test Movie (2024)/movie.mkv"],
    )

    assert result.status == "clean"
    assert result.moved is True
    deluge.remove_torrent.assert_awaited_once_with("a" * 40, remove_data=True)


@pytest.mark.asyncio
async def test_ingest_copy_failure_leaves_torrent_in_deluge():
    use_case, deluge = _build_use_case(copy_result=False)

    result = await use_case.execute(
        "a" * 40,
        _movie_download(),
        _scan_record(),
        "/quarantine/Test Movie (2024)",
        is_file=False,
        scanned_files=[],
    )

    assert result.status == "pending_move"
    assert result.moved is False
    deluge.remove_torrent.assert_not_awaited()
