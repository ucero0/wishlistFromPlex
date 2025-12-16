from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class PlexUserBase(BaseModel):
    name: str
    plex_token: str
    active: bool
    created_at: datetime
    updated_at: datetime

class CreatePlexUserRequest(PlexUserBase):
    name: str
    plex_token: str
class CreatePlexUserResponse(PlexUserBase):
    token_masked: str

class UpdatePlexUserRequest(PlexUserBase):
    name: Optional[str] = None
    plex_token: Optional[str] = None

