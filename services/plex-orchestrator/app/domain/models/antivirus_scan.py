"""Domain model for antivirus scan results."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class AntivirusScan(BaseModel):
    """Domain model for an antivirus scan result."""

    model_config = ConfigDict(from_attributes=False)

    id: Optional[int] = None
    prowlarr_guid: str
    file_path: Optional[str] = None
    source_folder_path: Optional[str] = None
    destination_folder_path: Optional[str] = None
    planned_destination_path: Optional[str] = None
    ingest_error: Optional[str] = None
    is_infected: bool = False
    scanned_at: datetime
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
