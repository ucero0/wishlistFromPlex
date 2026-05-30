"""HTTP schemas for external service errors and health."""
from pydantic import BaseModel, Field


class ExternalServiceErrorResponse(BaseModel):
    """Standard JSON body for external service failures."""

    service: str
    error_type: str = Field(
        ...,
        description="Machine-readable category, e.g. connection, not_found, operation",
    )
    detail: str
