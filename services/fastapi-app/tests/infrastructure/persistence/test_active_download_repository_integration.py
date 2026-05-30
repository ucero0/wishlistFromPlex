"""Integration tests for ActiveDownloadRepository mapping and session commit boundary."""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.composition.persistence import build_active_download_repository
from app.domain.models.active_download import ActiveDownload


@pytest.mark.asyncio
async def test_create_and_get_by_uid_roundtrip(db_session: AsyncSession):
    repo = build_active_download_repository(db_session)
    created = await repo.create(
        ActiveDownload(
            plex_guid="plex://movie/abc",
            watchlist_item_id="rating-1",
            plex_user_token="token-1",
            prowlarr_guid="prowlarr-guid-1",
            uid="a" * 40,
            title="Dune",
            file_name="Dune.mkv",
            year=2021,
            type="movie",
        )
    )
    await db_session.commit()

    found = await repo.get_by_uid("a" * 40)

    assert found is not None
    assert found.id == created.id
    assert found.plex_guid == "plex://movie/abc"
    assert found.watchlist_item_id == "rating-1"
    assert found.prowlarr_guid == "prowlarr-guid-1"
    assert found.file_name == "Dune.mkv"


@pytest.mark.asyncio
async def test_has_by_media_identity(db_session: AsyncSession):
    repo = build_active_download_repository(db_session)
    await repo.create(
        ActiveDownload(
            plex_guid="plex://movie/abc",
            prowlarr_guid="prowlarr-guid-1",
            uid="b" * 40,
            title="Dune",
            year=2021,
            type="movie",
        )
    )
    await db_session.commit()

    assert await repo.has_by_media_identity("Dune", 2021, "movie") is True
    assert await repo.has_by_media_identity("Dune", 2021, "tvshow") is False


@pytest.mark.asyncio
async def test_is_guid_plex_downloading(db_session: AsyncSession):
    repo = build_active_download_repository(db_session)
    assert await repo.is_guid_plex_downloading("plex://movie/not-yet") is False

    await repo.create(
        ActiveDownload(
            plex_guid="plex://movie/not-yet",
            prowlarr_guid="prowlarr-guid-dl",
            uid="d" * 40,
            title="Example",
            type="movie",
        )
    )
    await db_session.commit()

    assert await repo.is_guid_plex_downloading("plex://movie/not-yet") is True


@pytest.mark.asyncio
async def test_delete_by_id(db_session: AsyncSession):
    repo = build_active_download_repository(db_session)
    created = await repo.create(
        ActiveDownload(
            plex_guid="plex://movie/abc",
            prowlarr_guid="prowlarr-guid-1",
            uid="c" * 40,
            title="Dune",
            type="movie",
        )
    )
    await db_session.commit()

    deleted = await repo.delete_by_id(created.id)
    await db_session.commit()

    assert deleted is True
    assert await repo.get_by_id(created.id) is None
