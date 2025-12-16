from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class PlexUser(BaseModel):
    """Internal domain model for a Plex user."""
    id: Optional[int] = None
    name: str
    plex_token: str
    active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
