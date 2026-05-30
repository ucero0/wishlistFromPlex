"""HTTP schemas for TMDB connectivity checks."""
from pydantic import BaseModel


class TmdbConnectionResponse(BaseModel):
    connected: bool
    status: str
    service: str = "tmdb"
    error: str | None = None
    error_type: str | None = None
