"""Tests for ReconcileActiveDownloadsWithDelugeUseCase."""
import pytest

from app.application.pipelines.watchlist.use_cases.reconcile_active_downloads_with_deluge_use_case import (
    ReconcileActiveDownloadsWithDelugeUseCase,
)
from app.domain.errors.deluge import DelugeConnectionError
from app.domain.models.active_download import ActiveDownload
from app.domain.models.torrent import Torrent


def _db_row(uid: str, title: str = "Scrubs") -> ActiveDownload:
    return ActiveDownload(
        id=1,
        plex_guid="plex://show/1",
        prowlarr_guid="prowlarr-1",
        uid=uid,
        title=title,
        type="show",
        season=1,
        episode=1,
    )


class _FakeGetAll:
    def __init__(self, rows):
        self._rows = rows

    async def execute(self):
        return list(self._rows)


class _FakeGetDeluge:
    def __init__(self, torrents=None, error: Exception | None = None):
        self._torrents = torrents or []
        self._error = error

    async def execute(self):
        if self._error:
            raise self._error
        return list(self._torrents)


class _FakeDelete:
    def __init__(self):
        self.deleted: list[ActiveDownload] = []

    async def execute(self, row: ActiveDownload) -> None:
        self.deleted.append(row)


class _FakeUpdate:
    def __init__(self):
        self.updated: list[ActiveDownload] = []

    async def execute(self, row: ActiveDownload) -> ActiveDownload:
        self.updated.append(row)
        return row


@pytest.mark.asyncio
async def test_removes_db_rows_when_deluge_is_empty():
    row = _db_row("a" * 40)
    delete = _FakeDelete()
    use_case = ReconcileActiveDownloadsWithDelugeUseCase(
        get_all_active_downloads_query=_FakeGetAll([row]),
        get_torrents_status_query=_FakeGetDeluge([]),
        delete_active_download_use_case=delete,
        update_active_download_use_case=_FakeUpdate(),
    )

    result = await use_case.execute()

    assert result == {
        "removed_count": 1,
        "updated_count": 0,
        "total_checked": 1,
        "skipped": False,
    }
    assert delete.deleted == [row]


@pytest.mark.asyncio
async def test_removes_stale_db_rows_not_in_deluge():
    keep_uid = "b" * 40
    stale_uid = "c" * 40
    delete = _FakeDelete()
    update = _FakeUpdate()
    use_case = ReconcileActiveDownloadsWithDelugeUseCase(
        get_all_active_downloads_query=_FakeGetAll(
            [_db_row(stale_uid), _db_row(keep_uid)]
        ),
        get_torrents_status_query=_FakeGetDeluge(
            [Torrent(hash=keep_uid, file_name="show.mkv", state="Downloading")]
        ),
        delete_active_download_use_case=delete,
        update_active_download_use_case=update,
    )

    result = await use_case.execute()

    assert result["removed_count"] == 1
    assert result["updated_count"] == 1
    assert result["skipped"] is False
    assert len(delete.deleted) == 1
    assert delete.deleted[0].uid == stale_uid


@pytest.mark.asyncio
async def test_skips_when_deluge_unreachable():
    use_case = ReconcileActiveDownloadsWithDelugeUseCase(
        get_all_active_downloads_query=_FakeGetAll([_db_row("a" * 40)]),
        get_torrents_status_query=_FakeGetDeluge(
            error=DelugeConnectionError("connection refused")
        ),
        delete_active_download_use_case=_FakeDelete(),
        update_active_download_use_case=_FakeUpdate(),
    )

    result = await use_case.execute()

    assert result["skipped"] is True
    assert result["reason"] == "deluge_unavailable"
    assert result["removed_count"] == 0
