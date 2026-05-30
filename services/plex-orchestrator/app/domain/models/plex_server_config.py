"""Domain model for Plex Media Server admin credentials."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class PlexServerConfig(BaseModel):
    """Singleton server config (admin token for local Plex API)."""

    model_config = ConfigDict(from_attributes=True)

    id: int = 1
    admin_token: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
