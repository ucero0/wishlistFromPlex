"""Integration tests for AntivirusRepository."""
from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.composition.persistence import build_antivirus_repository
from app.domain.models.antivirus_scan import AntivirusScan


@pytest.mark.asyncio
async def test_create_and_get_by_guid_prowlarr(db_session: AsyncSession):
    repo = build_antivirus_repository(db_session)
    scanned_at = datetime.now(timezone.utc)
    created = await repo.create(
        AntivirusScan(
            prowlarr_guid="prow-av-1",
            file_path="/quarantine/movie.mkv",
            is_infected=False,
            scanned_at=scanned_at,
        )
    )
    await db_session.commit()

    rows = await repo.get_by_guid_prowlarr("prow-av-1")

    assert len(rows) == 1
    assert rows[0].id == created.id
    assert rows[0].prowlarr_guid == "prow-av-1"
    assert rows[0].file_path == "/quarantine/movie.mkv"
    assert rows[0].is_infected is False


@pytest.mark.asyncio
async def test_has_infected_by_guid_prowlarr(db_session: AsyncSession):
    repo = build_antivirus_repository(db_session)
    await repo.create(
        AntivirusScan(
            prowlarr_guid="prow-av-2",
            is_infected=True,
            scanned_at=datetime.now(timezone.utc),
        )
    )
    await db_session.commit()

    assert await repo.has_infected_by_guid_prowlarr("prow-av-2") is True
    assert await repo.has_infected_by_guid_prowlarr("prow-av-missing") is False
