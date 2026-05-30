"""Repository for Plex library paths."""
from datetime import datetime, timezone
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.plex_library_path import PlexLibraryPath, PlexLibraryPathMediaType
from app.domain.ports.repositories.plex.plex_library_path_repository_port import PlexLibraryPathRepoPort
from app.infrastructure.persistence.plex.models.plex_library_path_orm import PlexLibraryPathOrm


class PlexLibraryPathRepository(PlexLibraryPathRepoPort):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_active_by_media_type(
        self, media_type: PlexLibraryPathMediaType
    ) -> List[PlexLibraryPath]:
        result = await self.session.execute(
            select(PlexLibraryPathOrm)
            .where(PlexLibraryPathOrm.media_type == media_type)
            .where(PlexLibraryPathOrm.is_active.is_(True))
            .order_by(PlexLibraryPathOrm.path)
        )
        return [self._to_domain(row) for row in result.scalars().all()]

    async def list_all(self, *, active_only: bool = True) -> List[PlexLibraryPath]:
        stmt = select(PlexLibraryPathOrm).order_by(
            PlexLibraryPathOrm.media_type, PlexLibraryPathOrm.path
        )
        if active_only:
            stmt = stmt.where(PlexLibraryPathOrm.is_active.is_(True))
        result = await self.session.execute(stmt)
        return [self._to_domain(row) for row in result.scalars().all()]

    async def sync_from_server(self, paths: List[PlexLibraryPath]) -> int:
        now = datetime.now(timezone.utc)
        seen_keys: set[tuple[str, str]] = set()

        for path in paths:
            key = (path.section_id, path.path)
            seen_keys.add(key)
            result = await self.session.execute(
                select(PlexLibraryPathOrm).where(
                    PlexLibraryPathOrm.section_id == path.section_id,
                    PlexLibraryPathOrm.path == path.path,
                )
            )
            orm = result.scalar_one_or_none()
            if orm:
                orm.section_title = path.section_title
                orm.media_type = path.media_type
                orm.is_active = True
                orm.last_synced_at = now
            else:
                self.session.add(
                    PlexLibraryPathOrm(
                        section_id=path.section_id,
                        section_title=path.section_title,
                        media_type=path.media_type,
                        path=path.path,
                        is_active=True,
                        last_synced_at=now,
                    )
                )

        all_rows = await self.session.execute(select(PlexLibraryPathOrm))
        for orm in all_rows.scalars().all():
            if (orm.section_id, orm.path) not in seen_keys:
                orm.is_active = False

        await self.session.flush()

        active = await self.session.execute(
            select(PlexLibraryPathOrm).where(PlexLibraryPathOrm.is_active.is_(True))
        )
        return len(active.scalars().all())

    async def apply_disk_stats(self, paths: List[PlexLibraryPath]) -> int:
        now = datetime.now(timezone.utc)
        updated = 0
        for path in paths:
            if path.id is None:
                continue
            result = await self.session.execute(
                select(PlexLibraryPathOrm).where(PlexLibraryPathOrm.id == path.id)
            )
            orm = result.scalar_one_or_none()
            if orm is None:
                continue
            if path.disk_stats_error is None and path.total_bytes is not None:
                orm.volume_root = path.volume_root
                orm.total_bytes = path.total_bytes
                orm.used_bytes = path.used_bytes
                orm.free_bytes = path.free_bytes
                orm.used_percent = path.used_percent
                orm.disk_stats_error = None
                orm.disk_stats_synced_at = now
                updated += 1
            elif path.disk_stats_error:
                orm.disk_stats_error = path.disk_stats_error
                if path.volume_root:
                    orm.volume_root = path.volume_root
        await self.session.flush()
        return updated

    def _to_domain(self, orm: PlexLibraryPathOrm) -> PlexLibraryPath:
        return PlexLibraryPath(
            id=orm.id,
            section_id=orm.section_id,
            section_title=orm.section_title,
            media_type=orm.media_type,  # type: ignore[arg-type]
            path=orm.path,
            is_active=orm.is_active,
            last_synced_at=orm.last_synced_at,
            volume_root=orm.volume_root,
            total_bytes=orm.total_bytes,
            used_bytes=orm.used_bytes,
            free_bytes=orm.free_bytes,
            used_percent=orm.used_percent,
            disk_stats_synced_at=orm.disk_stats_synced_at,
            disk_stats_error=orm.disk_stats_error,
        )
