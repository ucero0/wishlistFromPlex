"""Integration tests for BlacklistActiveDownloadRepository."""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.composition.persistence import build_blacklist_torrent_repository
from app.domain.models.blacklist_torrent import BlacklistTorrent


@pytest.mark.asyncio
async def test_add_and_is_blacklisted(db_session: AsyncSession):
    repo = build_blacklist_torrent_repository(db_session)
    await repo.add(
        BlacklistTorrent(
            guid_prowlarr="prow-guid-1",
            reason="infected",
            name="Bad Torrent",
            year=2020,
            type="movie",
        )
    )
    await db_session.commit()

    assert await repo.is_blacklisted("prow-guid-1") is True
    assert await repo.is_blacklisted("other-guid") is False


@pytest.mark.asyncio
async def test_add_updates_existing_entry(db_session: AsyncSession):
    repo = build_blacklist_torrent_repository(db_session)
    await repo.add(
        BlacklistTorrent(guid_prowlarr="prow-guid-2", reason="unhealthy")
    )
    await db_session.commit()

    updated = await repo.add(
        BlacklistTorrent(guid_prowlarr="prow-guid-2", reason="infected", name="Title")
    )
    await db_session.commit()

    found = await repo.get_by_guid("prow-guid-2")

    assert updated.reason == "infected"
    assert found is not None
    assert found.reason == "infected"
    assert found.name == "Title"


@pytest.mark.asyncio
async def test_delete_by_guid(db_session: AsyncSession):
    repo = build_blacklist_torrent_repository(db_session)
    await repo.add(BlacklistTorrent(guid_prowlarr="prow-guid-3", reason="infected"))
    await db_session.commit()

    removed = await repo.delete_by_guid("prow-guid-3")
    await db_session.commit()

    assert removed is True
    assert await repo.is_blacklisted("prow-guid-3") is False
