"""Torrent waiting for download volume space before sending to Prowlarr/Deluge."""
from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

DeferredTorrentStatus = Literal["pending", "sent", "cancelled", "failed"]


class DeferredTorrentDownload(BaseModel):
    id: Optional[int] = None
    guid_plex: str
    rating_key: Optional[str] = None
    plex_user_token: Optional[str] = None
    guid_prowlarr: str
    indexer_id: int
    torrent_title: str
    media_title: str
    year: Optional[int] = None
    media_type: str
    search_query: Optional[str] = None
    size_bytes: Optional[int] = None
    magnet_url: Optional[str] = None
    status: DeferredTorrentStatus = "pending"
    defer_reason: Optional[str] = None
    attempt_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None

    def to_torrent_search_result(self):
        from app.domain.models.torrent_search import TorrentSearchResult, QualityInfo

        return TorrentSearchResult(
            title=self.torrent_title,
            guid=self.guid_prowlarr,
            indexerId=self.indexer_id,
            size=self.size_bytes,
            magnetUrl=self.magnet_url,
            quality_score=0,
            quality_info=QualityInfo(),
        )
