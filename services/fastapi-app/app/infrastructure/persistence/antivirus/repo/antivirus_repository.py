"""Repository for antivirus scan persistence operations."""
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.domain.models.antivirusScan import AntivirusScan
from app.domain.ports.repositories.antivirus.antivirusRepo import AntivirusRepoPort
from app.infrastructure.persistence.antivirus.model.antivirus_orm import AntivirusItem as AntivirusItemOrm


class AntivirusRepository(AntivirusRepoPort):
    """Repository for AntivirusScan domain model operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_id(self, antivirus_id: int) -> Optional[AntivirusScan]:
        """Get an antivirus scan by its ID."""
        orm = await self.session.get(AntivirusItemOrm, antivirus_id)
        return self._to_domain(orm) if orm else None
    
    async def get_by_guid_prowlarr(self, guid_prowlarr: str) -> List[AntivirusScan]:
        """Get all antivirus scans by Prowlarr GUID."""
        result = await self.session.execute(
            select(AntivirusItemOrm).where(AntivirusItemOrm.guidProwlarr == guid_prowlarr)
        )
        orms = result.scalars().all()
        return [self._to_domain(orm) for orm in orms]
    
    async def has_infected_by_guid_prowlarr(self, guid_prowlarr: str) -> bool:
        """Check if there are any infected files for a given Prowlarr GUID."""
        result = await self.session.execute(
            select(AntivirusItemOrm).where(
                AntivirusItemOrm.guidProwlarr == guid_prowlarr,
                AntivirusItemOrm.Infected == True
            )
        )
        return result.scalar_one_or_none() is not None
    
    async def get_by_file_path(self, file_path: str) -> Optional[AntivirusScan]:
        """Get an antivirus scan by file path."""
        result = await self.session.execute(
            select(AntivirusItemOrm).where(AntivirusItemOrm.filePath == file_path)
        )
        orm = result.scalar_one_or_none()
        return self._to_domain(orm) if orm else None
    
    async def get_infected_items(self) -> List[AntivirusScan]:
        """Get all infected items."""
        result = await self.session.execute(
            select(AntivirusItemOrm).where(AntivirusItemOrm.Infected == True)
        )
        orms = result.scalars().all()
        return [self._to_domain(orm) for orm in orms]
    
    async def get_clean_items(self) -> List[AntivirusScan]:
        """Get all clean (non-infected) items."""
        result = await self.session.execute(
            select(AntivirusItemOrm).where(AntivirusItemOrm.Infected == False)
        )
        orms = result.scalars().all()
        return [self._to_domain(orm) for orm in orms]
    
    async def get_all(self) -> List[AntivirusScan]:
        """Get all antivirus scans."""
        result = await self.session.execute(select(AntivirusItemOrm))
        orms = result.scalars().all()
        return [self._to_domain(orm) for orm in orms]
    
    async def create(self, antivirus_scan: AntivirusScan) -> AntivirusScan:
        """Create a new antivirus scan."""
        orm = self._to_orm(antivirus_scan)
        self.session.add(orm)
        await self.session.commit()
        await self.session.refresh(orm)
        return self._to_domain(orm)
    
    async def update(self, antivirus_scan: AntivirusScan) -> AntivirusScan:
        """Update an existing antivirus scan."""
        orm = await self.session.get(AntivirusItemOrm, antivirus_scan.id)
        if not orm:
            raise ValueError(f"Antivirus scan with id {antivirus_scan.id} not found")
        
        orm.guidProwlarr = antivirus_scan.guidProwlarr
        orm.filePath = antivirus_scan.filePath
        orm.folderPathSrc = antivirus_scan.folderPathSrc
        orm.folderPathDst = antivirus_scan.folderPathDst
        orm.Infected = antivirus_scan.Infected
        orm.scanDateTime = antivirus_scan.scanDateTime
        
        await self.session.commit()
        await self.session.refresh(orm)
        return self._to_domain(orm)
    
    async def delete(self, antivirus_scan: AntivirusScan) -> None:
        """Delete an antivirus scan."""
        orm = await self.session.get(AntivirusItemOrm, antivirus_scan.id)
        if orm:
            await self.session.delete(orm)
            await self.session.commit()
    
    async def delete_by_id(self, antivirus_id: int) -> bool:
        """Delete an antivirus scan by its ID. Returns True if deleted, False if not found."""
        orm = await self.session.get(AntivirusItemOrm, antivirus_id)
        if orm:
            await self.session.delete(orm)
            await self.session.commit()
            return True
        return False
    
    async def delete_by_guid_prowlarr(self, guid_prowlarr: str) -> int:
        """Delete all antivirus scans by Prowlarr GUID. Returns the number of deleted items."""
        result = await self.session.execute(
            select(AntivirusItemOrm).where(AntivirusItemOrm.guidProwlarr == guid_prowlarr)
        )
        orms = result.scalars().all()
        count = len(orms)
        for orm in orms:
            await self.session.delete(orm)
        await self.session.commit()
        return count
    
    # ---------- MAPPERS ----------
    
    def _to_domain(self, orm: AntivirusItemOrm) -> AntivirusScan:
        """Convert ORM model to domain model."""
        return AntivirusScan(
            id=orm.id,
            guidProwlarr=orm.guidProwlarr,
            filePath=orm.filePath,
            folderPathSrc=orm.folderPathSrc,
            folderPathDst=orm.folderPathDst,
            Infected=orm.Infected,
            scanDateTime=orm.scanDateTime,
            created_at=orm.created_at,
            updated_at=orm.updated_at,
        )
    
    def _to_orm(self, domain: AntivirusScan) -> AntivirusItemOrm:
        """Convert domain model to ORM model."""
        return AntivirusItemOrm(
            id=domain.id,
            guidProwlarr=domain.guidProwlarr,
            filePath=domain.filePath,
            folderPathSrc=domain.folderPathSrc,
            folderPathDst=domain.folderPathDst,
            Infected=domain.Infected,
            scanDateTime=domain.scanDateTime,
        )

