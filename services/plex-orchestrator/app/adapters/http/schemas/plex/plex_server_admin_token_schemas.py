"""HTTP schemas for Plex server admin token management."""
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class SetPlexServerAdminTokenRequest(BaseModel):
    admin_token: str = Field(
        ...,
        min_length=1,
        description="Plex server owner/admin X-Plex-Token",
    )


class PlexServerAdminTokenStatusResponse(BaseModel):
    configured: bool
    source: Literal["database", "environment", "none"]
    token_masked: Optional[str] = None
    updated_at: Optional[datetime] = None


class UpsertPlexServerAdminTokenResponse(BaseModel):
    configured: bool = True
    source: Literal["database"] = "database"
    token_masked: str
    updated_at: Optional[datetime] = None
    created: bool = Field(
        ...,
        description="True when the DB row was created; False when an existing row was updated",
    )
