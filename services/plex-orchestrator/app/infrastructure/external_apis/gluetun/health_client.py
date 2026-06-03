"""Gluetun VPN health HTTP client (independent of Deluge torrent state)."""
import httpx

from app.core.config import settings


class GluetunHealthClient:
    """
    Query Gluetun's internal health server.

    Gluetun runs TCP/TLS/ICMP checks to public targets through the VPN tunnel.
    Returns 200 when the tunnel works, 500 when it does not.
    """

    def __init__(self, base_url: str | None = None, timeout_seconds: float = 5.0):
        self.base_url = (base_url or settings.gluetun_health_url).rstrip("/")
        self.timeout_seconds = timeout_seconds

    def probe(self) -> tuple[bool, str | None]:
        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.get(f"{self.base_url}/")
            if response.status_code == 200:
                return True, None
            detail = (response.text or "").strip() or f"HTTP {response.status_code}"
            return False, f"Gluetun VPN unhealthy: {detail}"
        except httpx.HTTPError as exc:
            return False, f"Gluetun health unreachable at {self.base_url}: {exc}"
