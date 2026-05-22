"""Repository for deferred torrent downloads."""
from datetime import datetime, timezone

from typing import Optional

from sqlalchemy import func, select
from app.domain.services.media_identity import (
    normalize_media_type_for_queue_match,
    normalize_title,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.deferred_torrent_download import DeferredTorrentDownload
from app.domain.ports.repositories.deferredTorrent.deferredTorrentRepo import (
    DeferredTorrentRepoPort,
)
from app.infrastructure.persistence.deferredTorrent.models.deferredTorrentOrm import (
    DeferredTorrentDownloadOrm,
)


class DeferredTorrentRepository(DeferredTorrentRepoPort):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_pending_by_guid_plex(
        self, guid_plex: str
    ) -> DeferredTorrentDownload | None:
        result = await self.session.execute(
            select(DeferredTorrentDownloadOrm)
            .where(DeferredTorrentDownloadOrm.guid_plex == guid_plex)
            .where(DeferredTorrentDownloadOrm.status == "pending")
        )
        row = result.scalar_one_or_none()
        return self._to_domain(row) if row else None

    async def get_pending_by_guid_prowlarr(
        self, guid_prowlarr: str
    ) -> DeferredTorrentDownload | None:
        result = await self.session.execute(
            select(DeferredTorrentDownloadOrm)
            .where(DeferredTorrentDownloadOrm.guid_prowlarr == guid_prowlarr)
            .where(DeferredTorrentDownloadOrm.status == "pending")
        )
        row = result.scalar_one_or_none()
        return self._to_domain(row) if row else None

    async def get_pending_by_media_identity(
        self,
        title: str,
        year: Optional[int],
        media_type: str,
    ) -> DeferredTorrentDownload | None:
        norm_title = normalize_title(title)
        norm_type = normalize_media_type_for_queue_match(media_type)
        if not norm_title or not norm_type:
            return None

        type_values = ["movie"] if norm_type == "movie" else ["show", "tvshow"]

        stmt = (
            select(DeferredTorrentDownloadOrm)
            .where(DeferredTorrentDownloadOrm.status == "pending")
            .where(func.lower(DeferredTorrentDownloadOrm.media_title) == norm_title)
            .where(func.lower(DeferredTorrentDownloadOrm.media_type).in_(type_values))
        )
        if year is None:
            stmt = stmt.where(DeferredTorrentDownloadOrm.year.is_(None))
        else:
            stmt = stmt.where(DeferredTorrentDownloadOrm.year == year)

        result = await self.session.execute(stmt.limit(1))
        row = result.scalar_one_or_none()
        return self._to_domain(row) if row else None

    async def list_pending(self, *, limit: int = 50) -> list[DeferredTorrentDownload]:
        result = await self.session.execute(
            select(DeferredTorrentDownloadOrm)
            .where(DeferredTorrentDownloadOrm.status == "pending")
            .order_by(DeferredTorrentDownloadOrm.created_at)
            .limit(limit)
        )
        return [self._to_domain(r) for r in result.scalars().all()]

    async def upsert_pending(self, item: DeferredTorrentDownload) -> DeferredTorrentDownload:
        existing = await self.get_pending_by_guid_plex(item.guid_plex)
        if existing and existing.id:
            result = await self.session.execute(
                select(DeferredTorrentDownloadOrm).where(
                    DeferredTorrentDownloadOrm.id == existing.id
                )
            )
            orm = result.scalar_one()
            orm.guid_prowlarr = item.guid_prowlarr
            orm.indexer_id = item.indexer_id
            orm.torrent_title = item.torrent_title
            orm.media_title = item.media_title
            orm.year = item.year
            orm.media_type = item.media_type
            orm.search_query = item.search_query
            orm.size_bytes = item.size_bytes
            orm.magnet_url = item.magnet_url
            orm.defer_reason = item.defer_reason
            orm.rating_key = item.rating_key
            orm.plex_user_token = item.plex_user_token
            orm.status = "pending"
        else:
            orm = DeferredTorrentDownloadOrm(
                guid_plex=item.guid_plex,
                rating_key=item.rating_key,
                plex_user_token=item.plex_user_token,
                guid_prowlarr=item.guid_prowlarr,
                indexer_id=item.indexer_id,
                torrent_title=item.torrent_title,
                media_title=item.media_title,
                year=item.year,
                media_type=item.media_type,
                search_query=item.search_query,
                size_bytes=item.size_bytes,
                magnet_url=item.magnet_url,
                status="pending",
                defer_reason=item.defer_reason,
            )
            self.session.add(orm)
        await self.session.commit()
        await self.session.refresh(orm)
        return self._to_domain(orm)

    async def mark_sent(self, item_id: int) -> None:
        result = await self.session.execute(
            select(DeferredTorrentDownloadOrm).where(
                DeferredTorrentDownloadOrm.id == item_id
            )
        )
        orm = result.scalar_one_or_none()
        if orm:
            orm.status = "sent"
            orm.sent_at = datetime.now(timezone.utc)
            await self.session.commit()

    async def increment_attempt(self, item_id: int) -> None:
        result = await self.session.execute(
            select(DeferredTorrentDownloadOrm).where(
                DeferredTorrentDownloadOrm.id == item_id
            )
        )
        orm = result.scalar_one_or_none()
        if orm:
            orm.attempt_count = (orm.attempt_count or 0) + 1
            await self.session.commit()

    async def update(self, item: DeferredTorrentDownload) -> DeferredTorrentDownload:
        if item.id is None:
            raise ValueError("DeferredTorrentDownload.id required for update")
        result = await self.session.execute(
            select(DeferredTorrentDownloadOrm).where(
                DeferredTorrentDownloadOrm.id == item.id
            )
        )
        orm = result.scalar_one()
        orm.status = item.status
        orm.defer_reason = item.defer_reason
        orm.attempt_count = item.attempt_count
        orm.sent_at = item.sent_at
        await self.session.commit()
        await self.session.refresh(orm)
        return self._to_domain(orm)

    def _to_domain(self, orm: DeferredTorrentDownloadOrm) -> DeferredTorrentDownload:
        return DeferredTorrentDownload(
            id=orm.id,
            guid_plex=orm.guid_plex,
            rating_key=orm.rating_key,
            plex_user_token=orm.plex_user_token,
            guid_prowlarr=orm.guid_prowlarr,
            indexer_id=orm.indexer_id,
            torrent_title=orm.torrent_title,
            media_title=orm.media_title,
            year=orm.year,
            media_type=orm.media_type,
            search_query=orm.search_query,
            size_bytes=orm.size_bytes,
            magnet_url=orm.magnet_url,
            status=orm.status,  # type: ignore[arg-type]
            defer_reason=orm.defer_reason,
            attempt_count=orm.attempt_count or 0,
            created_at=orm.created_at,
            updated_at=orm.updated_at,
            sent_at=orm.sent_at,
        )
