"""Tests for scheduled Deluge ingest and health maintenance."""
from unittest.mock import AsyncMock, patch

import pytest

from app.application.pipelines.ingest.models.deluge_torrent_maintenance_result import (
    DelugeTorrentMaintenanceResult,
)
from app.application.pipelines.ingest.models.scan_and_ingest_torrent_result import (
    ScanAndIngestTorrentResult,
)
from app.application.pipelines.ingest.use_cases.process_deluge_torrents_use_case import (
    ProcessDelugeTorrentsUseCase,
)
from app.domain.models.active_download import ActiveDownload
from app.domain.models.torrent import Torrent

FIVE_DAYS_SECONDS = 5 * 86400


def _active_download(torrent_hash: str) -> ActiveDownload:
    return ActiveDownload(
        plex_guid="plex-guid",
        prowlarr_guid="prowlarr-guid",
        uid=torrent_hash,
        title="Test Show",
        type="show",
    )


def _use_case(**overrides):
    defaults = {
        "get_torrents_status_query": AsyncMock(),
        "get_all_active_downloads_query": AsyncMock(),
        "scan_and_ingest_torrent_use_case": AsyncMock(),
        "handle_unhealthy_torrent_use_case": AsyncMock(),
        "reconcile_active_downloads_use_case": AsyncMock(
            return_value={"updated_count": 1, "removed_count": 0, "skipped": False}
        ),
        "refresh_disk_stats_use_case": AsyncMock(),
    }
    defaults.update(overrides)
    return ProcessDelugeTorrentsUseCase(**defaults)


@pytest.mark.asyncio
async def test_runs_ingest_then_tracking_then_unhealthy_check():
    completed_hash = "a" * 40
    unhealthy_hash = "b" * 40
    completed = Torrent(
        hash=completed_hash,
        file_name="done.mkv",
        state="Seeding",
        progress=100.0,
    )
    unhealthy = Torrent(
        hash=unhealthy_hash,
        file_name="stuck.mkv",
        state="Downloading",
        progress=10.0,
        availability=0.2,
        time_since_download=FIVE_DAYS_SECONDS + 60,
    )
    get_status = AsyncMock(side_effect=[[completed, unhealthy], [unhealthy]])
    get_active = AsyncMock(
        side_effect=[
            [_active_download(completed_hash), _active_download(unhealthy_hash)],
            [_active_download(unhealthy_hash)],
        ]
    )
    scan_ingest = AsyncMock(
        return_value=ScanAndIngestTorrentResult(status="clean", moved=True)
    )
    handle_unhealthy = AsyncMock(return_value=True)
    reconcile = AsyncMock(
        side_effect=[
            {"updated_count": 2, "removed_count": 1, "skipped": False},
            {"updated_count": 0, "removed_count": 1, "skipped": False},
        ]
    )
    refresh_disk_stats = AsyncMock()

    use_case = _use_case(
        get_torrents_status_query=get_status,
        get_all_active_downloads_query=get_active,
        scan_and_ingest_torrent_use_case=scan_ingest,
        handle_unhealthy_torrent_use_case=handle_unhealthy,
        reconcile_active_downloads_use_case=reconcile,
        refresh_disk_stats_use_case=refresh_disk_stats,
    )

    with patch(
        "app.application.pipelines.ingest.use_cases.process_deluge_torrents_use_case.settings"
    ) as mock_settings:
        mock_settings.torrent_unhealthy_min_availability = 1.0
        mock_settings.torrent_unhealthy_no_transfer_days = 5
        result = await use_case.execute()

    assert result == DelugeTorrentMaintenanceResult(
        completed_checked=1,
        ingested=1,
        disk_stats_refreshed=True,
        tracking_updated=2,
        tracking_removed=2,
        unhealthy_checked=1,
        unhealthy_removed=1,
    )
    scan_ingest.execute.assert_awaited_once_with(completed_hash)
    handle_unhealthy.execute.assert_awaited_once()
    assert reconcile.await_count == 2
    refresh_disk_stats.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_skips_unhealthy_check_when_not_yet_finished():
    torrent_hash = "c" * 40
    torrents = [
        Torrent(
            hash=torrent_hash,
            file_name="active.mkv",
            state="Downloading",
            progress=50.0,
            availability=2.0,
            time_since_download=30,
        )
    ]
    get_status = AsyncMock(side_effect=[torrents, torrents])
    get_active = AsyncMock(return_value=[_active_download(torrent_hash)])
    handle_unhealthy = AsyncMock()

    use_case = _use_case(
        get_torrents_status_query=get_status,
        get_all_active_downloads_query=get_active,
        handle_unhealthy_torrent_use_case=handle_unhealthy,
    )

    with patch(
        "app.application.pipelines.ingest.use_cases.process_deluge_torrents_use_case.settings"
    ) as mock_settings:
        mock_settings.torrent_unhealthy_min_availability = 1.0
        mock_settings.torrent_unhealthy_no_transfer_days = 5
        result = await use_case.execute()

    assert result.unhealthy_checked == 0
    handle_unhealthy.execute.assert_not_awaited()
