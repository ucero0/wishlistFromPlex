"""Domain errors for Prowlarr integration."""
from app.domain.errors.external import ExternalServiceError


class ProwlarrError(ExternalServiceError):
    service = "prowlarr"


class ProwlarrConnectionError(ProwlarrError):
    """Prowlarr API is unreachable."""


class ProwlarrOperationError(ProwlarrError):
    """Prowlarr API call failed after connect."""


class ProwlarrDownloadError(ProwlarrError):
    """Failed to send torrent to download client via Prowlarr."""
