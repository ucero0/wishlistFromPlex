"""Repository for torrent persistence operations."""
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.domain.models.torrentDownload import TorrentDownload
from app.domain.ports.repositories.torrentDownload.torrentDownloadRepo import TorrentDownloadRepoPort
from app.infrastructure.persistence.torrentDownloads.model.torrent_orm import TorrentItem


class TorrentRepository(TorrentDownloadRepoPort):
    """Repository for TorrentDownload domain model operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_id(self, torrent_id: int) -> Optional[TorrentDownload]:
        """Get a torrent download by its ID."""
        orm = await self.session.get(TorrentItem, torrent_id)
        return self._to_domain(orm) if orm else None
    
    async def get_by_uid(self, torrent_uid: str) -> Optional[TorrentDownload]:
        """Get a torrent download by its UID."""
        result = await self.session.execute(
            select(TorrentItem).where(TorrentItem.uid == torrent_uid)
        )
        orm = result.scalar_one_or_none()
        return self._to_domain(orm) if orm else None
    
    async def get_by_guid_plex(self, guid_plex: str) -> List[TorrentDownload]:
        """Get all torrent downloads for a Plex GUID."""
        result = await self.session.execute(
            select(TorrentItem).where(TorrentItem.guidPlex == guid_plex)
        )
        orms = result.scalars().all()
        return [self._to_domain(orm) for orm in orms]
    
    async def is_guid_plex_downloading(self, guid_plex: str) -> bool:
        """Check if a Plex GUID has any active downloads."""
        result = await self.session.execute(
            select(TorrentItem).where(TorrentItem.guidPlex == guid_plex)
        )
        count = len(result.scalars().all())
        return count > 0
    
    async def get_by_guid_prowlarr(self, guid_prowlarr: str) -> Optional[TorrentDownload]:
        """Get a torrent download by its Prowlarr GUID."""
        result = await self.session.execute(
            select(TorrentItem).where(TorrentItem.guidProwlarr == guid_prowlarr)
        )
        orm = result.scalar_one_or_none()
        return self._to_domain(orm) if orm else None
    
    async def get_by_type(self, media_type: str) -> List[TorrentDownload]:
        """Get all torrent downloads by media type (movie or show)."""
        result = await self.session.execute(
            select(TorrentItem).where(TorrentItem.type == media_type)
        )
        orms = result.scalars().all()
        return [self._to_domain(orm) for orm in orms]
    
    async def get_all(self) -> List[TorrentDownload]:
        """Get all torrent downloads."""
        result = await self.session.execute(select(TorrentItem))
        orms = result.scalars().all()
        return [self._to_domain(orm) for orm in orms]
    
    async def create(self, torrent: TorrentDownload) -> TorrentDownload:
        """Create a new torrent download."""
        orm = self._to_orm(torrent)
        self.session.add(orm)
        await self.session.commit()
        await self.session.refresh(orm)
        return self._to_domain(orm)
    
    async def update(self, torrent: TorrentDownload) -> TorrentDownload:
        """Update an existing torrent download."""
        orm = await self.session.get(TorrentItem, torrent.id)
        if not orm:
            raise ValueError(f"Torrent download with id {torrent.id} not found")
        
        orm.guidPlex = torrent.guidPlex
        orm.ratingKey = torrent.ratingKey
        orm.plexUserToken = torrent.plexUserToken
        orm.guidProwlarr = torrent.guidProwlarr
        orm.uid = torrent.uid
        orm.title = torrent.title
        orm.fileName = torrent.fileName
        orm.year = torrent.year
        orm.type = torrent.type
        orm.season = torrent.season
        orm.episode = torrent.episode
        
        await self.session.commit()
        await self.session.refresh(orm)
        return self._to_domain(orm)
    
    async def delete(self, torrent: TorrentDownload) -> None:
        """Delete a torrent download."""
        orm = await self.session.get(TorrentItem, torrent.id)
        if orm:
            await self.session.delete(orm)
            await self.session.commit()
    
    async def delete_by_id(self, torrent_id: int) -> bool:
        """Delete a torrent download by its ID. Returns True if deleted, False if not found."""
        orm = await self.session.get(TorrentItem, torrent_id)
        if orm:
            await self.session.delete(orm)
            await self.session.commit()
            return True
        return False
    
    # ---------- MAPPERS ----------
    
    def _to_domain(self, orm: TorrentItem) -> TorrentDownload:
        """Convert ORM model to domain model."""
        return TorrentDownload(
            id=orm.id,
            guidPlex=orm.guidPlex,
            ratingKey=orm.ratingKey,
            plexUserToken=orm.plexUserToken,
            guidProwlarr=orm.guidProwlarr,
            uid=orm.uid,
            title=orm.title,
            fileName=orm.fileName,
            year=orm.year,
            type=orm.type,
            season=orm.season,
            episode=orm.episode,
            created_at=orm.created_at,
            updated_at=orm.updated_at,
        )
    
    def _to_orm(self, domain: TorrentDownload) -> TorrentItem:
        """Convert domain model to ORM model."""
        return TorrentItem(
            id=domain.id,
            guidPlex=domain.guidPlex,
            ratingKey=domain.ratingKey,
            plexUserToken=domain.plexUserToken,
            guidProwlarr=domain.guidProwlarr,
            uid=domain.uid,
            title=domain.title,
            fileName=domain.fileName,
            year=domain.year,
            type=domain.type,
            season=domain.season,
            episode=domain.episode,
        )

