from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.tmdb_user import TmdbUser
from app.domain.ports.repositories.tmdb.tmdb_user_repository_port import TmdbUserRepoPort
from app.infrastructure.persistence.tmdb.models.tmdb_user_orm import TmdbUserOrm


class TmdbUserRepository(TmdbUserRepoPort):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_by_id(self, user_id: int) -> TmdbUser | None:
        orm = await self.session.get(TmdbUserOrm, user_id)
        return self._to_domain(orm) if orm else None

    async def get_user_by_name(self, name: str) -> TmdbUser | None:
        result = await self.session.execute(
            select(TmdbUserOrm).where(TmdbUserOrm.name == name)
        )
        orm = result.scalar_one_or_none()
        return self._to_domain(orm) if orm else None

    async def get_user_by_access_token(self, access_token: str) -> TmdbUser | None:
        result = await self.session.execute(
            select(TmdbUserOrm).where(TmdbUserOrm.access_token == access_token)
        )
        orm = result.scalar_one_or_none()
        return self._to_domain(orm) if orm else None

    async def get_active_users(self) -> list[TmdbUser]:
        result = await self.session.execute(
            select(TmdbUserOrm).where(TmdbUserOrm.active.is_(True))
        )
        return [self._to_domain(orm) for orm in result.scalars().all()]

    async def create_user(self, user: TmdbUser) -> TmdbUser:
        orm = TmdbUserOrm(
            id=user.id,
            name=user.name,
            account_id=user.account_id,
            access_token=user.access_token,
            active=user.active,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
        self.session.add(orm)
        await self.session.flush()
        await self.session.refresh(orm)
        return self._to_domain(orm)

    async def update_user(self, user: TmdbUser) -> TmdbUser | None:
        orm = await self.session.get(TmdbUserOrm, user.id)
        if orm is None:
            return None
        orm.name = user.name
        orm.account_id = user.account_id
        orm.access_token = user.access_token
        orm.active = user.active
        orm.updated_at = user.updated_at
        await self.session.flush()
        await self.session.refresh(orm)
        return self._to_domain(orm)

    async def delete_user(self, user: TmdbUser) -> TmdbUser | None:
        orm = await self.session.get(TmdbUserOrm, user.id)
        if orm is None:
            return None
        deleted = self._to_domain(orm)
        await self.session.delete(orm)
        await self.session.flush()
        return deleted

    @staticmethod
    def _to_domain(orm: TmdbUserOrm) -> TmdbUser:
        return TmdbUser(
            id=orm.id,
            name=orm.name,
            account_id=orm.account_id,
            access_token=orm.access_token,
            active=orm.active,
            created_at=orm.created_at,
            updated_at=orm.updated_at,
        )
