"""Prowlarr HTTP schemas."""
from app.adapters.http.schemas.prowlarr.prowlarr_schemas import (
    SearchRequest,
    SearchByQueryRequest,
    SearchResponse,
    SearchResultResponse,
    SearchStatsResponse,
    ProwlarrConnectionResponse,
    ProwlarrIndexerCountResponse,
)

__all__ = [
    "SearchRequest",
    "SearchByQueryRequest",
    "SearchResponse",
    "SearchResultResponse",
    "SearchStatsResponse",
    "ProwlarrConnectionResponse",
    "ProwlarrIndexerCountResponse",
]
