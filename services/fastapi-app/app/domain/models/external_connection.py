"""Pydantic models for external service connection status."""
from pydantic import BaseModel, Field


class ExternalConnectionStatus(BaseModel):
    """Result of probing connectivity to an external service."""

    service: str = Field(..., description="Service identifier, e.g. deluge, prowlarr")
    connected: bool
    error: str | None = Field(
        default=None,
        description="Human-readable error when connected is False",
    )
    error_type: str | None = Field(
        default=None,
        description="Machine-readable category when connected is False, e.g. connection, server_auth",
    )
    version: str | None = Field(
        default=None,
        description="Remote service version when available (e.g. Prowlarr)",
    )

    @property
    def is_healthy(self) -> bool:
        return self.connected
