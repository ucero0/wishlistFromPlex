"""Resolved Plex library identifiers for a media item."""
from pydantic import BaseModel, ConfigDict


class PlexLibraryIdentity(BaseModel):
    """Plex server guid and rating key when the title exists in a local library."""

    model_config = ConfigDict(frozen=True)

    plex_guid: str
    rating_key: str | None = None
