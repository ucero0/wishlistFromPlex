"""Tests for Deluge adapter connection probe."""
from unittest.mock import MagicMock, patch

import pytest

from app.adapters.external.deluge.adapter import DelugeAdapter
from app.domain.errors.deluge import DelugeConnectionError
from app.infrastructure.external_apis.deluge.schemas import ExternalDelugeTorrentStatusResponse


@pytest.mark.asyncio
async def test_connection_reports_vpn_unhealthy_without_using_torrents():
    client = MagicMock()
    client.probe_connection = MagicMock()
    adapter = DelugeAdapter(client)

    with patch(
        "app.adapters.external.deluge.adapter.probe_deluge_path_health"
    ) as probe:
        from app.domain.services.deluge_path_health import DelugePathHealth

        probe.return_value = DelugePathHealth(
            vpn_required=True,
            vpn_healthy=False,
            error="Gluetun VPN unhealthy",
        )
        status = await adapter.test_connection()

    assert status.connected is True
    assert status.vpn_healthy is False
    client.get_session_status.assert_not_called()


@pytest.mark.asyncio
async def test_connection_rpc_failure_skips_vpn_and_swarm():
    client = MagicMock()
    client.probe_connection.side_effect = DelugeConnectionError("down")
    adapter = DelugeAdapter(client)
    status = await adapter.test_connection()

    assert status.connected is False
