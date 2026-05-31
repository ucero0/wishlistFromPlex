from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class TmdbUser(BaseModel):
    """TMDB account used for watchlist automation."""

    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    name: str
    account_id: Optional[int] = None
    access_token: str
    active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
