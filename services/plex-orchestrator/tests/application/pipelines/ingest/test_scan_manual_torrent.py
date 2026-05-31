"""Tests for scan/ingest of manual Deluge torrents."""
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.pipelines.ingest.queries.resolve_torrent_for_ingest_query import (
    ResolvedTorrentForIngest,
)
from app.application.pipelines.ingest.use_cases.scan_torrent_use_case import (
    ScanTorrentUseCase,
)
from app.domain.models.active_download import ActiveDownload
from app.domain.models.antivirus_scan import AntivirusScan
from app.domain.models.scan_result import ScanResult


def _manual_active() -> ActiveDownload:
    return ActiveDownload(
        plex_guid="manual://torrent/abc",
        prowlarr_guid="manual:abc",
        uid="abc",
        title="Manual Movie",
        file_name="Manual.Movie.mkv",
        type="movie",
    )


@pytest.mark.asyncio
async def test_scan_torrent_resolves_manual_deluge_torrent():
    resolved = ResolvedTorrentForIngest(
        active_download=_manual_active(), is_manual=True
    )
    resolve = AsyncMock()
    resolve.execute = AsyncMock(return_value=resolved)
    filesystem = MagicMock()
    filesystem.get_quarantine_file_path.return_value = "/quarantine/Manual.Movie.mkv"
    filesystem.path_exists.return_value = True
    filesystem.is_file.return_value = True
    filesystem.is_directory.return_value = False
    filesystem.remove_non_media_files.return_value = 0
    antivirus = MagicMock()
    antivirus.scan.return_value = ScanResult(
        is_infected=False, scanned_files=["/quarantine/Manual.Movie.mkv"]
    )
    repo = AsyncMock()
    repo.create = AsyncMock(
        return_value=AntivirusScan(
            prowlarr_guid="manual:abc",
            file_path="/quarantine/Manual.Movie.mkv",
            is_infected=False,
            scanned_at=datetime.now(),
        )
    )
    use_case = ScanTorrentUseCase(resolve, filesystem, antivirus, repo)

    result = await use_case.execute("abc", title="Manual Movie", media_type="movie")

    assert result.status == "clean"
    assert result.is_manual is True
    assert result.torrent_download is not None
    assert result.torrent_download.prowlarr_guid == "manual:abc"
    resolve.execute.assert_awaited_once_with(
        "abc", media_type="movie", title="Manual Movie", year=None
    )
