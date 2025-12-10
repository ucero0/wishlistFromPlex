"""Orchestration module Pydantic schemas."""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class OrchestrationRunResponse(BaseModel):
    """Schema for orchestration run response."""
    success: bool
    sync_summary: Dict[str, Any]
    items_processed: int
    items_searched: int
    items_added_to_deluge: int
    errors: List[str]
    run_time: str
    details: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class OrchestrationStatsResponse(BaseModel):
    """Schema for orchestration statistics."""
    total_runs: int
    last_run_time: Optional[datetime] = None
    total_items_processed: int
    total_items_searched: int
    total_items_added: int
    average_run_duration_seconds: Optional[float] = None

    class Config:
        from_attributes = True

