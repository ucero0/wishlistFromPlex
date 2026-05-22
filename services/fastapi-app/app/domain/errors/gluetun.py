"""Domain errors for Gluetun VPN integration."""
from app.domain.errors.external import ExternalServiceError


class GluetunError(ExternalServiceError):
    """Base Gluetun-related error."""

    service = "gluetun"


class GluetunConnectionError(GluetunError):
    """Gluetun health server is unreachable."""


class GluetunUnhealthyError(GluetunError):
    """Gluetun is reachable but reports an unhealthy VPN state."""

    def __init__(self, message: str, *, health_detail: str | None = None):
        self.health_detail = health_detail
        super().__init__(message)
