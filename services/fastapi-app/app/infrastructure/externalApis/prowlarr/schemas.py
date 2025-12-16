"""Prowlarr external API schemas."""
from __future__ import annotations
import logging
from pydantic import BaseModel, Field, model_validator
from typing import Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class ProwlarrStatusResponse(BaseModel):
    """Prowlarr connection status (external API response)."""
    connected: bool
    version: Optional[str] = None
    indexer_count: int = 0
    error: Optional[str] = None


class ProwlarrRawResult(BaseModel):
    """Raw result from Prowlarr API (external API response)."""
    title: str
    indexer: str = "Unknown"
    size: Optional[int] = 0
    seeders: Optional[int] = Field(default=0)
    leechers: Optional[int] = 0
    magnetUrl: Optional[str] = None
    downloadUrl: Optional[str] = None
    infoUrl: Optional[str] = None
    publishDate: Optional[datetime] = None
    guid: Optional[str] = None
    indexerId: Optional[int] = None
    protocol: Optional[str] = None  # Download protocol (torrent, magnet, etc.)

    @model_validator(mode='before')
    @classmethod
    def normalize_seeders_field(cls, data: Any) -> Any:
        """Normalize seeders field from different possible field names."""
        if isinstance(data, dict):
            # Handle different field names for seeders (seeders, seedCount, seeds)
            if "seeders" not in data or data.get("seeders") is None:
                if "seedCount" in data:
                    data["seeders"] = data.get("seedCount", 0)
                elif "seeds" in data:
                    data["seeders"] = data.get("seeds", 0)
        return data

    class Config:
        populate_by_name = True  # Allow both field name and alias
        extra = "ignore"  # Ignore extra fields from Prowlarr
