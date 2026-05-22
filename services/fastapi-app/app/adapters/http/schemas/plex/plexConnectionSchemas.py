"""HTTP schemas for Plex connectivity checks."""
from pydantic import BaseModel


class PlexConnectionResponse(BaseModel):
    connected: bool
    status: str
    service: str = "plex"
    error: str | None = None
