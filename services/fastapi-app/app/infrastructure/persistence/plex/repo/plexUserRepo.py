"""Repository for media persistence operations."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.domain.models.plexUser import PlexUser
from app.domain.ports.repositories.plex.plexUserRepo import PlexUserRepoPort
from app.infrastructure.persistence.plex.models.plexUserOrm import PlexUserOrm

class PlexUserRepo(PlexUserRepoPort):
    """Repository for Plex user persistence operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # ---------- READ ----------

    async def get_user_by_id(self, user_id: int) -> PlexUser | None:
        orm = await self.session.get(PlexUserOrm, user_id)
        return self._to_domain(orm) if orm else None

    async def get_user_by_name(self, name: str) -> PlexUser | None:
        result = await self.session.execute(
            select(PlexUserOrm).where(PlexUserOrm.name == name)
        )
        orm = result.scalar_one_or_none()
        return self._to_domain(orm) if orm else None

    async def get_active_users(self) -> list[PlexUser]:
        result = await self.session.execute(
            select(PlexUserOrm).where(PlexUserOrm.active.is_(True))
        )
        return [self._to_domain(orm) for orm in result.scalars().all()]

    # ---------- WRITE ----------

    async def create_user(self, user: PlexUser) -> PlexUser:
        orm = PlexUserOrm(
            id=user.id,
            name=user.name,
            plex_token=user.plex_token,
            active=user.active,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
        self.session.add(orm)
        await self.session.commit()
        await self.session.refresh(orm)
        return self._to_domain(orm)

    async def update_user(self, user: PlexUser) -> PlexUser | None:
        orm = await self.session.get(PlexUserOrm, user.id)
        if orm is None:
            return None

        orm.name = user.name
        orm.plex_token = user.plex_token
        orm.active = user.active
        orm.updated_at = user.updated_at

        await self.session.commit()
        await self.session.refresh(orm)
        return self._to_domain(orm)

    # ---------- MAPPERS ----------

    def _to_domain(self, orm: PlexUserOrm) -> PlexUser:
        return PlexUser(
            id=orm.id,
            name=orm.name,
            plex_token=orm.plex_token,
            active=orm.active,
            created_at=orm.created_at,
            updated_at=orm.updated_at,
        )