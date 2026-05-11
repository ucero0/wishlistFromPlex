"""Domain model for search indexer metadata."""
from pydantic import BaseModel


class ProwlarrIndexerInfo(BaseModel):
    """Minimal domain-safe indexer info used by application logic."""
    id: int
    name: str
    enabled: bool

