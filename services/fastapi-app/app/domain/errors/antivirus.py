"""Domain errors for Antivirus scan service integration."""
from app.domain.errors.external import ExternalServiceError


class AntivirusError(ExternalServiceError):
    service = "antivirus"


class AntivirusConnectionError(AntivirusError):
    """Antivirus HTTP scan service is unreachable."""


class AntivirusOperationError(AntivirusError):
    """Antivirus scan request failed."""


class AntivirusPathNotFoundError(AntivirusError):
    """Scan path does not exist on the filesystem."""
