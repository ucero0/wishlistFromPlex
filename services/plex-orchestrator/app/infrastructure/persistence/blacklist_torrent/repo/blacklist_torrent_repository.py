"""Repository for blacklist torrent persistence."""
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.blacklist_torrent import BlacklistTorrent
from app.domain.ports.repositories.blacklist_torrent.blacklist_torrent_repo import (
    BlacklistTorrentRepoPort,
)
from app.infrastructure.persistence.blacklist_torrent.model.blacklist_torrent_orm import (
    BlacklistTorrentOrm,
)


class BlacklistActiveDownloadRepository(BlacklistTorrentRepoPort):
    """Repository for BlacklistTorrent domain model."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def is_blacklisted(self, guid_prowlarr: str) -> bool:
        result = await self.session.execute(
            select(BlacklistTorrentOrm).where(
                BlacklistTorrentOrm.guid_prowlarr == guid_prowlarr
            )
        )
        return result.scalar_one_or_none() is not None

    async def add(self, blacklist_torrent: BlacklistTorrent) -> BlacklistTorrent:
        existing = await self.get_by_guid(blacklist_torrent.guid_prowlarr)
        if existing:
            # Update reason and optional display fields if already listed
            orm = await self.session.get(BlacklistTorrentOrm, existing.id)
            if orm:
                orm.reason = blacklist_torrent.reason
                orm.name = blacklist_torrent.name
                orm.year = blacklist_torrent.year
                orm.type = blacklist_torrent.type
                await self.session.flush()
                await self.session.refresh(orm)
                return self._to_domain(orm)
        orm = BlacklistTorrentOrm(
            guid_prowlarr=blacklist_torrent.guid_prowlarr,
            reason=blacklist_torrent.reason,
            name=blacklist_torrent.name,
            year=blacklist_torrent.year,
            type=blacklist_torrent.type,
        )
        self.session.add(orm)
        await self.session.flush()
        await self.session.refresh(orm)
        return self._to_domain(orm)

    async def get_by_guid(self, guid_prowlarr: str) -> Optional[BlacklistTorrent]:
        result = await self.session.execute(
            select(BlacklistTorrentOrm).where(
                BlacklistTorrentOrm.guid_prowlarr == guid_prowlarr
            )
        )
        orm = result.scalars().first()
        return self._to_domain(orm) if orm else None

    async def get_all(self) -> List[BlacklistTorrent]:
        result = await self.session.execute(
            select(BlacklistTorrentOrm).order_by(BlacklistTorrentOrm.created_at.desc())
        )
        rows = result.scalars().all()
        return [self._to_domain(orm) for orm in rows]

    async def delete_by_guid(self, guid_prowlarr: str) -> bool:
        result = await self.session.execute(
            select(BlacklistTorrentOrm).where(
                BlacklistTorrentOrm.guid_prowlarr == guid_prowlarr
            )
        )
        orm = result.scalars().first()
        if orm:
            await self.session.delete(orm)
            await self.session.flush()
            return True
        return False

    def _to_domain(self, orm: BlacklistTorrentOrm) -> BlacklistTorrent:
        return BlacklistTorrent(
            id=orm.id,
            guid_prowlarr=orm.guid_prowlarr,
            reason=orm.reason,
            name=orm.name,
            year=orm.year,
            type=orm.type,
            created_at=orm.created_at,
        )
