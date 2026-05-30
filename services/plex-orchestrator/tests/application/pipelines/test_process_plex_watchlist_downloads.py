"""Tests for ProcessPlexWatchlistDownloadsUseCase error isolation."""
from unittest.mock import MagicMock

import pytest

from app.application.pipelines.watchlist.models.watchlist_download_run_result import (
    WatchlistItemProcessOutcome,
)
from app.application.pipelines.watchlist.use_cases.process_plex_watchlist_downloads_use_case import (
    ProcessPlexWatchlistDownloadsUseCase,
)
from app.domain.models.media import MediaItem, MediaType
from app.domain.models.watchlist_item_for_user import WatchlistItemForUser


def _entry(title: str, rating_key: str) -> WatchlistItemForUser:
    return WatchlistItemForUser(
        item=MediaItem(
            guid=f"plex://movie/{rating_key}",
            rating_key=rating_key,
            title=title,
            year=2024,
            type=MediaType.MOVIE,
        ),
        plex_user_id=1,
        plex_user_token="token",
    )


class _FakeGetWatchlists:
    def __init__(self, entries):
        self._entries = entries

    async def execute(self):
        return self._entries


class _FakeDeferred:
    async def execute(self):
        class R:
            sent = 0
            still_pending = 0

        return R()


class _FakeReconcile:
    async def execute(self):
        return {"removed_count": 0, "updated_count": 0, "total_checked": 0}


class _FakeShouldSkip:
    async def execute(self, entry):
        return False, None


class _FakeProcessItem:
    def __init__(self, outcomes_by_title):
        self._outcomes = outcomes_by_title

    async def execute(self, entry):
        title = entry.item.title
        if title in self._outcomes and isinstance(self._outcomes[title], Exception):
            raise self._outcomes[title]
        return self._outcomes.get(title, WatchlistItemProcessOutcome.SENT_TO_DELUGE)


@pytest.mark.asyncio
async def test_continues_processing_after_item_raises():
    entries = [_entry("Fails", "1"), _entry("Works", "2")]
    use_case = ProcessPlexWatchlistDownloadsUseCase(
        get_plex_user_query=MagicMock(),
        get_watchlist_query=MagicMock(),
        reconcile_active_downloads_use_case=_FakeReconcile(),
        process_deferred_downloads_use_case=_FakeDeferred(),
        should_skip_watchlist_item_query=_FakeShouldSkip(),
        process_watchlist_item_use_case=_FakeProcessItem(
            {"Fails": RuntimeError("Prowlarr down"), "Works": WatchlistItemProcessOutcome.SENT_TO_DELUGE}
        ),
    )
    use_case._get_watchlists_for_active_users = _FakeGetWatchlists(entries)

    result = await use_case.execute()

    assert result.watchlist_entries == 2
    assert result.send_failed == 1
    assert result.sent_to_deluge == 1
