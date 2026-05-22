"""Base errors for external service integrations."""


class ExternalServiceError(Exception):
    """Base exception for failures talking to an external system."""

    service: str = "external"

    def __init__(self, message: str, *, service: str | None = None):
        self.message = message
        if service is not None:
            self.service = service
        super().__init__(message)
