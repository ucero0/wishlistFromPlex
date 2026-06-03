"""Tests for Deluge VPN path health (Gluetun, independent of torrents)."""
from unittest.mock import MagicMock, patch

from app.domain.services.deluge_path_health import (
    probe_deluge_path_health,
    should_skip_unhealthy_removal,
)


def test_no_vpn_when_deluge_host_is_deluge():
    with patch("app.domain.services.deluge_path_health.settings") as mock_settings:
        mock_settings.deluge_host = "deluge"
        health = probe_deluge_path_health(mock_settings)

    assert health.vpn_required is False
    assert health.vpn_healthy is True
    assert should_skip_unhealthy_removal(health, skip_when_vpn_down=True) is False


def test_gluetun_healthy():
    client = MagicMock()
    client.probe.return_value = (True, None)
    with patch("app.domain.services.deluge_path_health.settings") as mock_settings:
        mock_settings.deluge_host = "gluetun"
        health = probe_deluge_path_health(mock_settings, health_client=client)

    assert health.vpn_required is True
    assert health.vpn_healthy is True
    assert should_skip_unhealthy_removal(health, skip_when_vpn_down=True) is False


def test_gluetun_unhealthy_skips_removal():
    client = MagicMock()
    client.probe.return_value = (False, "Gluetun VPN unhealthy: timeout")
    with patch("app.domain.services.deluge_path_health.settings") as mock_settings:
        mock_settings.deluge_host = "gluetun"
        health = probe_deluge_path_health(mock_settings, health_client=client)

    assert health.vpn_healthy is False
    assert should_skip_unhealthy_removal(health, skip_when_vpn_down=True) is True
