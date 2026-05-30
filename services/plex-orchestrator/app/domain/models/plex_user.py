from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class PlexUser(BaseModel):
    """Internal domain model for a Plex user."""
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    name: str
    plex_token: str
    active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

