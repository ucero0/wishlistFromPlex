"""Tests for ProcessWatchlistItemUseCase."""
import pytest
from app.application.pipelines.watchlist.use_cases.process_watchlist_item_use_case import (
    ProcessWatchlistItemUseCase,
)
from app.domain.models.torrent import Torrent
from app.domain.models.active_download import ActiveDownload
from app.domain.models.media import MediaItem, MediaType
from app.domain.models.torrent_search import QualityInfo, TorrentSearchResult
from app.domain.models.watchlist_item_for_user import WatchlistItemForUser


class _FakeBuildSearchQuery:
    async def execute(self, watchlist):
        return f"{watchlist.title} {watchlist.year}"


class _FakeFindBestTorrent:
    def __init__(self, results):
        self._results = results

    async def execute(self, search_query):
        return self._results


class _FakeTryDownload:
    def __init__(self, outcomes):
        self._outcomes = list(outcomes)
        self.calls = 0

    async def execute(self, torrent_result, watchlist, user_token, search_query):
        self.calls += 1
        return self._outcomes[self.calls - 1]


class _FakeCreateActiveDownload:
    def __init__(self):
        self.created: list[ActiveDownload] = []

    async def execute(self, torrent_download: ActiveDownload):
        self.created.append(torrent_download)
        return torrent_download


class _FakeRemoveWatchlist:
    def __init__(self):
        self.removed: list[tuple] = []

    async def execute(self, rating_key, user_token):
        self.removed.append((rating_key, user_token))


def _entry(**kwargs):
    defaults = dict(
        title="Dune",
        guid="plex://movie/1",
        rating_key="123",
        year=2021,
        type=MediaType.MOVIE,
        plex_user_id=1,
        plex_user_token="plex-token",
    )
    defaults.update(kwargs)
    return WatchlistItemForUser(
        item=MediaItem(
            guid=defaults["guid"],
            rating_key=defaults["rating_key"],
            title=defaults["title"],
            year=defaults["year"],
            type=defaults["type"],
        ),
        plex_user_id=defaults["plex_user_id"],
        plex_user_token=defaults["plex_user_token"],
    )


def _torrent_result(guid="prowlarr-1"):
    return TorrentSearchResult(
        guid=guid,
        title="Dune 2021 1080p",
        indexer="Indexer",
        indexerId=1,
        size=10_000_000_000,
        seeders=100,
        leechers=5,
        quality_score=100,
        quality_info=QualityInfo(),
    )


@pytest.mark.asyncio
async def test_process_watchlist_item_downloads_first_successful_torrent():
    create_uc = _FakeCreateActiveDownload()
    remove_uc = _FakeRemoveWatchlist()
    try_download = _FakeTryDownload(
        [
            (True, Torrent(hash="a" * 40, file_name="Dune.mkv", state="Downloading"), False),
        ]
    )
    use_case = ProcessWatchlistItemUseCase(
        watchlist_search_query_builder=_FakeBuildSearchQuery(),
        find_best_torrent_query=_FakeFindBestTorrent([_torrent_result()]),
        try_send_torrent_use_case=try_download,
        create_active_download_use_case=create_uc,
        remove_watchlist_item_use_case=remove_uc,
    )

    ok = await use_case.execute(_entry())

    assert ok is True
    assert try_download.calls == 1
    assert len(create_uc.created) == 1
    assert create_uc.created[0].uid == "a" * 40
    assert create_uc.created[0].plex_guid == "plex://movie/1"
    assert remove_uc.removed == [("123", "plex-token")]


@pytest.mark.asyncio
async def test_process_watchlist_item_tries_next_result_on_failure():
    try_download = _FakeTryDownload(
        [
            (False, None, False),
            (True, Torrent(hash="b" * 40, file_name="Dune.mkv", state="Downloading"), False),
        ]
    )
    use_case = ProcessWatchlistItemUseCase(
        watchlist_search_query_builder=_FakeBuildSearchQuery(),
        find_best_torrent_query=_FakeFindBestTorrent(
            [_torrent_result("bad"), _torrent_result("good")]
        ),
        try_send_torrent_use_case=try_download,
        create_active_download_use_case=_FakeCreateActiveDownload(),
        remove_watchlist_item_use_case=_FakeRemoveWatchlist(),
    )

    ok = await use_case.execute(_entry())

    assert ok is True
    assert try_download.calls == 2


@pytest.mark.asyncio
async def test_process_watchlist_item_returns_true_when_deferred():
    use_case = ProcessWatchlistItemUseCase(
        watchlist_search_query_builder=_FakeBuildSearchQuery(),
        find_best_torrent_query=_FakeFindBestTorrent([_torrent_result()]),
        try_send_torrent_use_case=_FakeTryDownload([(False, None, True)]),
        create_active_download_use_case=_FakeCreateActiveDownload(),
        remove_watchlist_item_use_case=_FakeRemoveWatchlist(),
    )

    ok = await use_case.execute(_entry())

    assert ok is True


@pytest.mark.asyncio
async def test_process_watchlist_item_returns_false_when_no_search_results():
    use_case = ProcessWatchlistItemUseCase(
        watchlist_search_query_builder=_FakeBuildSearchQuery(),
        find_best_torrent_query=_FakeFindBestTorrent([]),
        try_send_torrent_use_case=_FakeTryDownload([]),
        create_active_download_use_case=_FakeCreateActiveDownload(),
        remove_watchlist_item_use_case=_FakeRemoveWatchlist(),
    )

    ok = await use_case.execute(_entry())

    assert ok is False
