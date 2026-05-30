"""HTTP schemas for Plex connectivity checks."""
from typing import Literal, Optional

from pydantic import BaseModel


class PlexConnectionResponse(BaseModel):
    connected: bool
    status: str
    service: str = "plex"
    error: str | None = None
    error_type: Optional[
        Literal["connection", "server_auth", "configuration", "operation"]
    ] = None
