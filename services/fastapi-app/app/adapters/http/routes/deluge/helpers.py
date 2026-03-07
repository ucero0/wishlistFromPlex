"""Helpers for Deluge HTTP routes: 404 handling and domain → response mapping."""
from typing import List, Optional

from fastapi import HTTPException, status

from app.adapters.http.schemas.deluge.delugeSchemas import DelugeTorrentStatusResponse
from app.domain.models.torrent import Torrent

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------
DETAIL_TORRENT_NOT_FOUND = "Torrent not found in deluge"
DETAIL_TORRENT_NAME_NOT_FOUND = "Torrent name not found in deluge"
DETAIL_NO_TORRENTS_FOUND = "No torrents found in deluge"

# -----------------------------------------------------------------------------
# Ensure found (raise 404 if missing / empty)
# -----------------------------------------------------------------------------


def ensure_torrent_found(
    torrent: Optional[Torrent],
    detail: str = DETAIL_TORRENT_NOT_FOUND,
) -> Torrent:
    """Return the torrent or raise HTTP 404 if None."""
    if torrent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
        )
    return torrent


def ensure_torrents_found(
    torrents: List[Torrent],
    detail: str = DETAIL_NO_TORRENTS_FOUND,
) -> List[Torrent]:
    """Return the list or raise HTTP 404 if empty."""
    if not torrents:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
        )
    return torrents


# -----------------------------------------------------------------------------
# Domain → response mapping
# -----------------------------------------------------------------------------


def to_torrent_response(torrent: Torrent) -> DelugeTorrentStatusResponse:
    """Map domain Torrent to HTTP response schema."""
    return DelugeTorrentStatusResponse(**torrent.model_dump())


def to_torrent_responses(torrents: List[Torrent]) -> List[DelugeTorrentStatusResponse]:
    """Map list of domain Torrents to HTTP response schema."""
    return [to_torrent_response(t) for t in torrents]
