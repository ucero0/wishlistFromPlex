from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class CreateTmdbUserRequest(BaseModel):
    name: str
    access_token: str
    account_id: Optional[int] = None


class CreateTmdbUserResponse(BaseModel):
    name: str
    account_id: int
    active: bool
    created_at: datetime
    updated_at: datetime
    token_masked: str


class UpdateTmdbUserRequest(BaseModel):
    name: Optional[str] = None
    access_token: Optional[str] = None
    account_id: Optional[int] = None
    active: Optional[bool] = None
