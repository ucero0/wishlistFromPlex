"""Domain model for antivirus scan results."""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AntivirusScan(BaseModel):
    """Domain model for an antivirus scan result."""
    id: Optional[int] = None
    guidProwlarr: str
    filePath: Optional[str] = None
    folderPathSrc: Optional[str] = None
    folderPathDst: Optional[str] = None
    Infected: bool = False
    scanDateTime: datetime
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

