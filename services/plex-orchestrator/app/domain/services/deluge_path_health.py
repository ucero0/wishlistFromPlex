"""Deluge download path health (VPN) — independent of per-torrent status."""
from dataclasses import dataclass

from app.core.config import Settings, settings
from app.infrastructure.external_apis.gluetun.health_client import GluetunHealthClient


@dataclass(frozen=True)
class DelugePathHealth:
    """Whether the Deluge download path (VPN when using Gluetun) is healthy."""

    vpn_required: bool
    vpn_healthy: bool
    error: str | None = None


def _uses_gluetun_vpn(deluge_host: str) -> bool:
    return deluge_host.strip().lower() == "gluetun"


def probe_deluge_path_health(
    app_settings: Settings | None = None,
    *,
    health_client: GluetunHealthClient | None = None,
) -> DelugePathHealth:
    """
    Check VPN/internet for the Deluge download path without reading torrents.

    - DELUGE_HOST=gluetun → GET Gluetun :9999 health (tunnel probes to Cloudflare/GitHub)
    - DELUGE_HOST=deluge (no-vpn) → always healthy (no VPN layer in this stack)
    """
    cfg = app_settings or settings
    if not _uses_gluetun_vpn(cfg.deluge_host):
        return DelugePathHealth(vpn_required=False, vpn_healthy=True)

    client = health_client or GluetunHealthClient()
    healthy, error = client.probe()
    return DelugePathHealth(
        vpn_required=True,
        vpn_healthy=healthy,
        error=error,
    )


def should_skip_unhealthy_removal(path_health: DelugePathHealth, *, skip_when_vpn_down: bool) -> bool:
    if not skip_when_vpn_down:
        return False
    return path_health.vpn_required and not path_health.vpn_healthy
