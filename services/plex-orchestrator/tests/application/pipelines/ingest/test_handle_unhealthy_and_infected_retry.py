"""Tests for unhealthy/infected failure handlers."""
from unittest.mock import AsyncMock

import pytest

from app.application.pipelines.ingest.models.retry_active_download_outcome import (
    RetryActiveDownloadOutcome,
)
from app.application.pipelines.ingest.models.scan_and_ingest_torrent_result import (
    ScanAndIngestTorrentResult,
)
from app.application.pipelines.ingest.use_cases.handle_infected_torrent_use_case import (
    HandleInfectedTorrentUseCase,
)
from app.application.pipelines.ingest.use_cases.handle_unhealthy_torrent_use_case import (
    HandleUnhealthyTorrentUseCase,
)
from app.domain.models.active_download import ActiveDownload
from app.domain.models.scan_result import ScanResult
from app.domain.models.torrent import Torrent

FIVE_DAYS_SECONDS = 5 * 86400


def _active() -> ActiveDownload:
    return ActiveDownload(
        id=1,
        plex_guid="plex://movie/1",
        prowlarr_guid="prowlarr-old",
        uid="a" * 40,
        title="Dune",
        year=2021,
        type="movie",
    )


def _unhealthy_torrent() -> Torrent:
    return Torrent(
        hash="a" * 40,
        file_name="dune.mkv",
        state="Downloading",
        progress=10.0,
        availability=0.0,
        time_since_download=FIVE_DAYS_SECONDS + 60,
    )


@pytest.mark.asyncio
async def test_handle_unhealthy_blacklists_removes_and_readds_watchlist():
    deluge = AsyncMock()
    deluge.remove_torrent = AsyncMock()
    blacklist = AsyncMock()
    blacklist.execute = AsyncMock()
    readd = AsyncMock()
    readd.execute = AsyncMock()
    use_case = HandleUnhealthyTorrentUseCase(deluge, blacklist, readd)

    handled = await use_case.execute(
        _unhealthy_torrent(),
        _active(),
        min_availability=1.0,
        no_transfer_days=5,
    )

    assert handled is True
    blacklist.execute.assert_awaited_once()
    deluge.remove_torrent.assert_awaited_once_with("a" * 40, remove_data=True)
    readd.execute.assert_awaited_once_with(_active())


@pytest.mark.asyncio
async def test_handle_unhealthy_returns_false_for_healthy_torrent():
    torrent = Torrent(
        hash="a" * 40,
        file_name="dune.mkv",
        state="Downloading",
        progress=50.0,
        availability=5.0,
        time_since_download=60,
    )
    use_case = HandleUnhealthyTorrentUseCase(
        AsyncMock(), AsyncMock(), AsyncMock()
    )

    handled = await use_case.execute(
        torrent, _active(), min_availability=1.0, no_transfer_days=5
    )

    assert handled is False


@pytest.mark.asyncio
async def test_handle_infected_blacklists_removes_and_retries():
    deluge = AsyncMock()
    deluge.remove_torrent = AsyncMock(return_value=True)
    blacklist = AsyncMock()
    blacklist.execute = AsyncMock()
    retry = AsyncMock()
    retry.execute = AsyncMock(return_value=RetryActiveDownloadOutcome.SUCCESS)
    reconcile = AsyncMock()
    reconcile.execute = AsyncMock(
        return_value={"removed_count": 0, "updated_count": 0, "total_checked": 1}
    )
    use_case = HandleInfectedTorrentUseCase(
        deluge, blacklist, retry, reconcile
    )
    scan = ScanResult(
        is_infected=True,
        infected_files=["/quarantine/bad.exe"],
        virus_name="EICAR",
        scanned_files=["/quarantine/bad.exe"],
    )

    result = await use_case.execute("a" * 40, _active(), scan)

    assert isinstance(result, ScanAndIngestTorrentResult)
    assert result.status == "infected"
    assert result.deleted is True
    blacklist.execute.assert_awaited_once()
    deluge.remove_torrent.assert_awaited_once_with("a" * 40, remove_data=True)
    retry.execute.assert_awaited_once()
    reconcile.execute.assert_awaited_once()
