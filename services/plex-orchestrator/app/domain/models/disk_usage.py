"""Disk space statistics for a volume or mount."""
from pydantic import BaseModel


class DiskUsageStats(BaseModel):
    """Bytes reported by the OS for the filesystem containing a path."""

    total_bytes: int
    used_bytes: int
    free_bytes: int
