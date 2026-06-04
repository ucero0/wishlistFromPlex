"""Domain model for rapid media file integrity verification."""
from pydantic import BaseModel, Field


class MediaIntegrityResult(BaseModel):
    """Outcome of probing one or more video files before library ingest."""

    is_valid: bool
    checked_files: list[str] = Field(default_factory=list)
    corrupt_files: list[str] = Field(default_factory=list)
    file_errors: dict[str, str] = Field(default_factory=dict)

    @property
    def summary_message(self) -> str:
        if self.is_valid:
            return f"Verified {len(self.checked_files)} media file(s)"
        if not self.corrupt_files:
            return "Media integrity check failed"
        if len(self.corrupt_files) == 1:
            path = self.corrupt_files[0]
            detail = self.file_errors.get(path, "unreadable or corrupt")
            return f"Corrupt media file: {path} ({detail})"
        return f"Found {len(self.corrupt_files)} corrupt media file(s)"
