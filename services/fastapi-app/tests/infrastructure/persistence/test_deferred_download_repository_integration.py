"""Integration tests for DeferredDownloadRepository."""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.composition.persistence import build_deferred_download_repository
from app.domain.models.deferred_download import DeferredDownload


def _pending_item(**overrides) -> DeferredDownload:
    base = {
        "guid_plex": "plex://movie/deferred-1",
        "guid_prowlarr": "prow-deferred-1",
        "indexer_id": 1,
        "torrent_title": "Dune 2021 1080p",
        "media_title": "Dune",
        "year": 2021,
        "media_type": "movie",
    }
    base.update(overrides)
    return DeferredDownload(**base)


@pytest.mark.asyncio
async def test_upsert_and_get_pending_by_guid_plex(db_session: AsyncSession):
    repo = build_deferred_download_repository(db_session)
    created = await repo.upsert_pending(_pending_item())
    await db_session.commit()

    found = await repo.get_pending_by_guid_plex("plex://movie/deferred-1")

    assert found is not None
    assert found.id == created.id
    assert found.guid_prowlarr == "prow-deferred-1"
    assert found.status == "pending"


@pytest.mark.asyncio
async def test_get_pending_by_media_identity(db_session: AsyncSession):
    repo = build_deferred_download_repository(db_session)
    await repo.upsert_pending(_pending_item())
    await db_session.commit()

    found = await repo.get_pending_by_media_identity("Dune", 2021, "movie")

    assert found is not None
    assert found.media_title == "Dune"


@pytest.mark.asyncio
async def test_mark_sent_clears_pending_lookup(db_session: AsyncSession):
    repo = build_deferred_download_repository(db_session)
    created = await repo.upsert_pending(_pending_item())
    await db_session.commit()

    await repo.mark_sent(created.id)
    await db_session.commit()

    assert await repo.get_pending_by_guid_plex("plex://movie/deferred-1") is None
    pending = await repo.list_pending()
    assert pending == []
