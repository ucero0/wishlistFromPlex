"""Domain model for antivirus scan results."""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime


class AntivirusScan(BaseModel):
    """Domain model for an antivirus scan result."""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: Optional[int] = None
    prowlarr_guid: str = Field(alias="guidProwlarr")
    file_path: Optional[str] = Field(default=None, alias="filePath")
    source_folder_path: Optional[str] = Field(default=None, alias="folderPathSrc")
    destination_folder_path: Optional[str] = Field(default=None, alias="folderPathDst")
    planned_destination_path: Optional[str] = Field(
        default=None, alias="plannedDestination"
    )
    ingest_error: Optional[str] = Field(default=None, alias="ingestError")
    is_infected: bool = Field(default=False, alias="Infected")
    scanned_at: datetime = Field(alias="scanDateTime")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

