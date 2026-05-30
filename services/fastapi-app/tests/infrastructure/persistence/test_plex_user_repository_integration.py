"""Integration tests for PlexUserRepository."""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.composition.persistence import build_plex_user_repository
from app.domain.models.plex_user import PlexUser


@pytest.mark.asyncio
async def test_create_and_get_active_users(db_session: AsyncSession):
    repo = build_plex_user_repository(db_session)
    await repo.create_user(
        PlexUser(name="alice", plex_token="token-a", active=True)
    )
    await repo.create_user(
        PlexUser(name="bob", plex_token="token-b", active=False)
    )
    await db_session.commit()

    active = await repo.get_active_users()

    assert len(active) == 1
    assert active[0].name == "alice"
    assert active[0].plex_token == "token-a"


@pytest.mark.asyncio
async def test_get_user_by_name(db_session: AsyncSession):
    repo = build_plex_user_repository(db_session)
    await repo.create_user(
        PlexUser(name="carol", plex_token="token-c", active=True)
    )
    await db_session.commit()

    user = await repo.get_user_by_name("carol")

    assert user is not None
    assert user.plex_token == "token-c"
