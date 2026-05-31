"""Repository for torrent persistence operations."""
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import exists, func, or_, select
from app.domain.models.active_download import ActiveDownload
from app.domain.services.media_identity import (
    normalize_media_type_for_queue_match,
    normalize_title,
)
from app.domain.ports.repositories.active_downloads.active_download_repository_port import ActiveDownloadRepositoryPort
from app.infrastructure.persistence.active_downloads.model.active_download_orm import ActiveDownloadOrm


class ActiveDownloadRepository(ActiveDownloadRepositoryPort):
    """Repository for ActiveDownload domain model operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_id(self, torrent_id: int) -> Optional[ActiveDownload]:
        """Get a torrent download by its ID."""
        orm = await self.session.get(ActiveDownloadOrm, torrent_id)
        return self._to_domain(orm) if orm else None
    
    async def get_by_uid(self, torrent_uid: str) -> Optional[ActiveDownload]:
        """Get a torrent download by its UID."""
        result = await self.session.execute(
            select(ActiveDownloadOrm).where(ActiveDownloadOrm.uid == torrent_uid)
        )
        orm = result.scalar_one_or_none()
        return self._to_domain(orm) if orm else None
    
    async def get_by_guid_plex(self, guid_plex: str) -> List[ActiveDownload]:
        """Get all torrent downloads for a Plex GUID."""
        result = await self.session.execute(
            select(ActiveDownloadOrm).where(ActiveDownloadOrm.guidPlex == guid_plex)
        )
        orms = result.scalars().all()
        return [self._to_domain(orm) for orm in orms]
    
    async def is_guid_plex_downloading(self, guid_plex: str) -> bool:
        """Check if a watchlist or Plex library GUID has any active downloads."""
        stmt = select(
            exists().where(
                or_(
                    ActiveDownloadOrm.guidPlex == guid_plex,
                    ActiveDownloadOrm.plexGuid == guid_plex,
                )
            )
        )
        result = await self.session.execute(stmt)
        return bool(result.scalar())
    
    async def get_by_guid_prowlarr(self, guid_prowlarr: str) -> Optional[ActiveDownload]:
        """Get a torrent download by its Prowlarr GUID."""
        result = await self.session.execute(
            select(ActiveDownloadOrm).where(ActiveDownloadOrm.guidProwlarr == guid_prowlarr)
        )
        orm = result.scalar_one_or_none()
        return self._to_domain(orm) if orm else None

    async def has_by_media_identity(
        self,
        title: str,
        year: Optional[int],
        media_type: str,
    ) -> bool:
        norm_title = normalize_title(title)
        norm_type = normalize_media_type_for_queue_match(media_type)
        if not norm_title or not norm_type:
            return False

        type_values = {norm_type}
        if norm_type == "show":
            type_values.add("tvshow")

        stmt = select(ActiveDownloadOrm).where(
            func.lower(ActiveDownloadOrm.title) == norm_title,
            ActiveDownloadOrm.type.in_(type_values),
        )
        if year is None:
            stmt = stmt.where(ActiveDownloadOrm.year.is_(None))
        else:
            stmt = stmt.where(ActiveDownloadOrm.year == year)

        result = await self.session.execute(stmt.limit(1))
        return result.scalar_one_or_none() is not None

    async def has_episode_queued(
        self,
        plex_guid: str,
        title: str,
        season: int,
        episode: int,
    ) -> bool:
        norm_title = normalize_title(title)
        type_values = {"show", "tvshow"}
        identity_clauses = [
            ActiveDownloadOrm.guidPlex == plex_guid,
            ActiveDownloadOrm.plexGuid == plex_guid,
        ]
        if norm_title:
            identity_clauses.append(func.lower(ActiveDownloadOrm.title) == norm_title)

        stmt = select(ActiveDownloadOrm).where(
            ActiveDownloadOrm.season == season,
            ActiveDownloadOrm.episode == episode,
            ActiveDownloadOrm.type.in_(type_values),
            or_(*identity_clauses),
        )
        result = await self.session.execute(stmt.limit(1))
        return result.scalar_one_or_none() is not None

    async def get_by_type(self, media_type: str) -> List[ActiveDownload]:
        """Get all torrent downloads by media type (movie or show)."""
        result = await self.session.execute(
            select(ActiveDownloadOrm).where(ActiveDownloadOrm.type == media_type)
        )
        orms = result.scalars().all()
        return [self._to_domain(orm) for orm in orms]
    
    async def get_all(self) -> List[ActiveDownload]:
        """Get all torrent downloads."""
        result = await self.session.execute(select(ActiveDownloadOrm))
        orms = result.scalars().all()
        return [self._to_domain(orm) for orm in orms]
    
    async def create(self, torrent: ActiveDownload) -> ActiveDownload:
        """Create a new torrent download."""
        orm = self._to_orm(torrent)
        self.session.add(orm)
        await self.session.flush()
        await self.session.refresh(orm)
        return self._to_domain(orm)
    
    async def update(self, torrent: ActiveDownload) -> ActiveDownload:
        """Update an existing torrent download."""
        orm = await self.session.get(ActiveDownloadOrm, torrent.id)
        if not orm:
            raise ValueError(f"Torrent download with id {torrent.id} not found")
        
        orm.guidPlex = torrent.plex_guid
        orm.plexGuid = torrent.plex_library_guid
        orm.ratingKey = torrent.watchlist_item_id
        orm.plexUserToken = torrent.plex_user_token
        orm.watchlistSource = torrent.watchlist_source
        orm.tmdbMediaId = torrent.tmdb_media_id
        orm.tmdbAccountId = torrent.tmdb_account_id
        orm.guidProwlarr = torrent.prowlarr_guid
        orm.uid = torrent.uid
        orm.title = torrent.title
        orm.fileName = torrent.file_name
        orm.year = torrent.year
        orm.type = torrent.type
        orm.season = torrent.season
        orm.episode = torrent.episode
        
        await self.session.flush()
        await self.session.refresh(orm)
        return self._to_domain(orm)
    
    async def delete(self, torrent: ActiveDownload) -> None:
        """Delete a torrent download."""
        orm = await self.session.get(ActiveDownloadOrm, torrent.id)
        if orm:
            await self.session.delete(orm)
            await self.session.flush()
    
    async def delete_by_id(self, torrent_id: int) -> bool:
        """Delete a torrent download by its ID. Returns True if deleted, False if not found."""
        orm = await self.session.get(ActiveDownloadOrm, torrent_id)
        if orm:
            await self.session.delete(orm)
            await self.session.flush()
            return True
        return False
    
    # ---------- MAPPERS ----------
    
    def _to_domain(self, orm: ActiveDownloadOrm) -> ActiveDownload:
        """Convert ORM model to domain model."""
        return ActiveDownload(
            id=orm.id,
            plex_guid=orm.guidPlex,
            plex_library_guid=orm.plexGuid,
            watchlist_item_id=orm.ratingKey,
            plex_user_token=orm.plexUserToken,
            watchlist_source=orm.watchlistSource,
            tmdb_media_id=orm.tmdbMediaId,
            tmdb_account_id=orm.tmdbAccountId,
            prowlarr_guid=orm.guidProwlarr,
            uid=orm.uid,
            title=orm.title,
            file_name=orm.fileName,
            year=orm.year,
            type=orm.type,
            season=orm.season,
            episode=orm.episode,
            created_at=orm.created_at,
            updated_at=orm.updated_at,
        )
    
    def _to_orm(self, domain: ActiveDownload) -> ActiveDownloadOrm:
        """Convert domain model to ORM model."""
        return ActiveDownloadOrm(
            id=domain.id,
            guidPlex=domain.plex_guid,
            plexGuid=domain.plex_library_guid,
            ratingKey=domain.watchlist_item_id,
            plexUserToken=domain.plex_user_token,
            watchlistSource=domain.watchlist_source,
            tmdbMediaId=domain.tmdb_media_id,
            tmdbAccountId=domain.tmdb_account_id,
            guidProwlarr=domain.prowlarr_guid,
            uid=domain.uid,
            title=domain.title,
            fileName=domain.file_name,
            year=domain.year,
            type=domain.type,
            season=domain.season,
            episode=domain.episode,
        )

