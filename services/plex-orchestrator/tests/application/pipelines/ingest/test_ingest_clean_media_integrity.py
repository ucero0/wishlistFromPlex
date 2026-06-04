"""Tests for media integrity gate in clean-torrent ingest."""
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.pipelines.ingest.models.scan_and_ingest_torrent_result import (
    ScanAndIngestTorrentResult,
)
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


@pytest.mark.asyncio
async def test_ingest_skips_copy_when_media_corrupt():
    filesystem = MagicMock()
    filesystem.list_video_files.return_value = []
    filesystem.copy.return_value = True
    deluge = AsyncMock()
    destination_selector = AsyncMock()
    destination_selector.select = AsyncMock(
        return_value=MagicMock(path="/plex/movies", section_id=1)
    )
    destination_resolver = MagicMock()
    destination_resolver.resolve.return_value = "/plex/movies/Test.mkv"
    verify = MagicMock()
    verify.execute.return_value = MediaIntegrityResult(
        is_valid=False,
        checked_files=["/quarantine/bad.mkv"],
        corrupt_files=["/quarantine/bad.mkv"],
        file_errors={"/quarantine/bad.mkv": "truncated"},
    )
    handle_corrupt = AsyncMock()
    handle_corrupt.execute = AsyncMock(
        return_value=ScanAndIngestTorrentResult(
            status="corrupt",
            message="Corrupt media file",
            corrupt_files=["/quarantine/bad.mkv"],
        )
    )

    use_case = IngestCleanTorrentUseCase(
        filesystem_service=filesystem,
        antivirus_repo=AsyncMock(),
        deluge_provider=deluge,
        destination_selector=destination_selector,
        destination_resolver=destination_resolver,
        partial_scan_library_use_case=AsyncMock(),
        sync_library_paths_use_case=AsyncMock(),
        refresh_disk_stats_use_case=AsyncMock(),
        reconcile_active_downloads_use_case=AsyncMock(),
        remove_watchlist_entry_use_case=AsyncMock(),
        verify_media_integrity_use_case=verify,
        handle_corrupt_media_use_case=handle_corrupt,
    )

    result = await use_case.execute(
        "a" * 40,
        _movie_download(),
        _scan_record(),
        "/quarantine/Test Movie (2024)",
        is_file=False,
        scanned_files=[],
    )

    assert result.status == "corrupt"
    filesystem.copy.assert_not_called()
    handle_corrupt.execute.assert_awaited_once()
    deluge.remove_torrent.assert_not_awaited()
