"""Tests for scheduled Deluge ingest and health maintenance."""
import time
from unittest.mock import AsyncMock, MagicMock, patch

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
from app.domain.models.torrent_health_config import TorrentHealthConfig
from app.domain.services.deluge_path_health import DelugePathHealth

FIVE_DAYS_SECONDS = 5 * 86400
ONE_DAY_SECONDS = 86400

DEFAULT_HEALTH_CONFIG = TorrentHealthConfig(
    grace_hours=0,
    unfinishable_days=1,
    no_complete_copy_days=2,
    no_complete_zero_hours=6,
    stall_no_peers_hours=24,
    stall_days=5,
    skip_when_vpn_unhealthy=True,
    use_strict_when_vpn_healthy=False,
)


def _active_download(torrent_hash: str) -> ActiveDownload:
    return ActiveDownload(
        plex_guid="plex-guid",
        prowlarr_guid="prowlarr-guid",
        uid=torrent_hash,
        title="Test Show",
        type="show",
    )


def _use_case(**overrides):
    health_service = AsyncMock()
    health_service.get_config = AsyncMock(return_value=DEFAULT_HEALTH_CONFIG)
    defaults = {
        "get_torrents_status_query": AsyncMock(),
        "get_all_active_downloads_query": AsyncMock(),
        "scan_and_ingest_torrent_use_case": AsyncMock(),
        "handle_unhealthy_torrent_use_case": AsyncMock(),
        "reconcile_active_downloads_use_case": AsyncMock(
            return_value={"updated_count": 1, "removed_count": 0, "skipped": False}
        ),
        "refresh_disk_stats_use_case": AsyncMock(),
        "torrent_health_config_service": health_service,
    }
    defaults.update(overrides)
    return ProcessDelugeTorrentsUseCase(**defaults)


@pytest.mark.asyncio
async def test_runs_ingest_then_unhealthy_then_tracking():
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
        time_added=time.time() - ONE_DAY_SECONDS - 60,
        num_seeds=0,
        num_peers=0,
    )
    get_status = AsyncMock()
    get_status.execute = AsyncMock(
        side_effect=[[completed, unhealthy], [unhealthy]],
    )
    get_active = AsyncMock()
    get_active.execute = AsyncMock(
        side_effect=[
            [_active_download(completed_hash), _active_download(unhealthy_hash)],
            [_active_download(unhealthy_hash)],
        ]
    )
    scan_ingest = AsyncMock()
    scan_ingest.execute = AsyncMock(
        return_value=ScanAndIngestTorrentResult(status="clean", moved=True)
    )
    handle_unhealthy = AsyncMock()
    handle_unhealthy.execute = AsyncMock(return_value=True)
    reconcile = AsyncMock()
    reconcile.execute = AsyncMock(
        return_value={"updated_count": 2, "removed_count": 0, "skipped": False}
    )
    refresh_disk_stats = AsyncMock()

    health_service = AsyncMock()
    health_service.get_config = AsyncMock(
        return_value=DEFAULT_HEALTH_CONFIG.model_copy(
            update={"skip_when_vpn_unhealthy": False}
        )
    )

    use_case = _use_case(
        get_torrents_status_query=get_status,
        get_all_active_downloads_query=get_active,
        scan_and_ingest_torrent_use_case=scan_ingest,
        handle_unhealthy_torrent_use_case=handle_unhealthy,
        reconcile_active_downloads_use_case=reconcile,
        refresh_disk_stats_use_case=refresh_disk_stats,
        torrent_health_config_service=health_service,
    )

    vpn_ok = DelugePathHealth(vpn_required=True, vpn_healthy=True)

    with patch(
        "app.application.pipelines.ingest.use_cases.process_deluge_torrents_use_case.probe_deluge_path_health",
        return_value=vpn_ok,
    ):
        result = await use_case.execute()

    assert result.unhealthy_removed == 1
    handle_unhealthy.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_skips_unhealthy_when_vpn_down_even_if_torrents_look_dead():
    torrent_hash = "d" * 40
    dead = Torrent(
        hash=torrent_hash,
        file_name="dead.mkv",
        state="Downloading",
        progress=0.0,
        last_seen_complete=0,
        num_seeds=0,
        num_peers=0,
        time_added=time.time() - (25 * 3600),
    )
    get_status = AsyncMock()
    get_status.execute = AsyncMock(side_effect=[[], [dead]])
    get_active = AsyncMock()
    get_active.execute = AsyncMock(return_value=[_active_download(torrent_hash)])
    handle_unhealthy = AsyncMock()

    use_case = _use_case(
        get_torrents_status_query=get_status,
        get_all_active_downloads_query=get_active,
        handle_unhealthy_torrent_use_case=handle_unhealthy,
    )

    vpn_down = DelugePathHealth(
        vpn_required=True,
        vpn_healthy=False,
        error="Gluetun VPN unhealthy",
    )

    with patch(
        "app.application.pipelines.ingest.use_cases.process_deluge_torrents_use_case.probe_deluge_path_health",
        return_value=vpn_down,
    ):
        result = await use_case.execute()

    assert result.unhealthy_skipped_vpn_unhealthy is True
    assert result.vpn_healthy is False
    handle_unhealthy.execute.assert_not_awaited()
