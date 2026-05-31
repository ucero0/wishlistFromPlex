"""Tests for ProcessWatchlistItemUseCase."""
import pytest
from app.application.pipelines.watchlist.models.watchlist_download_run_result import (
    WatchlistItemProcessOutcome,
)
from app.application.pipelines.watchlist.use_cases.process_watchlist_item_use_case import (
    ProcessWatchlistItemUseCase,
)
from app.domain.models.torrent import Torrent
from app.domain.models.active_download import ActiveDownload
from app.domain.models.media import MediaItem, MediaType
from app.domain.models.torrent_search import QualityInfo, TorrentSearchResult
from app.domain.models.watchlist_item_for_user import WatchlistItemForUser
from app.domain.models.tv_episode import TvEpisode


class _FakeFindBestTorrent:
    def __init__(self, results):
        self._results = results
        self.calls: list[tuple] = []

    async def execute(self, search_query, media_type="movie"):
        self.calls.append((search_query, media_type))
        return self._results


class _FakeBuildSearchQuery:
    async def execute(self, watchlist):
        return f"{watchlist.title} {watchlist.year}"

    def build_tv_episode_search_query(self, watchlist, season, episode):
        return f"{watchlist.title} S{season:02d}E{episode:02d}"


class _FakeGetMissingTvEpisodes:
    def __init__(self, missing=None, download_missing=None):
        self._missing = missing if missing is not None else []
        self._download_missing = download_missing

    async def execute(self, watchlist, user_token, *, for_download=False):
        if for_download and self._download_missing is not None:
            return list(self._download_missing)
        return list(self._missing)


class _FakeTryDownload:
    def __init__(self, outcomes):
        self._outcomes = list(outcomes)
        self.calls = 0

    async def execute(
        self, torrent_result, entry, search_query, **kwargs
    ):
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
        self.removed: list[WatchlistItemForUser] = []

    async def execute(self, entry: WatchlistItemForUser):
        self.removed.append(entry)


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
        remove_watchlist_entry_use_case=remove_uc,
        get_missing_tv_episodes_query=_FakeGetMissingTvEpisodes(),
    )

    outcome = await use_case.execute(_entry())

    assert try_download.calls == 1
    assert outcome == WatchlistItemProcessOutcome.SENT_TO_DELUGE
    assert len(create_uc.created) == 1
    assert create_uc.created[0].plex_guid == "plex://movie/1"
    assert create_uc.created[0].watchlist_item_id == "123"
    assert len(remove_uc.removed) == 0


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
        remove_watchlist_entry_use_case=_FakeRemoveWatchlist(),
        get_missing_tv_episodes_query=_FakeGetMissingTvEpisodes(),
    )

    outcome = await use_case.execute(_entry())

    assert outcome == WatchlistItemProcessOutcome.SENT_TO_DELUGE
    assert try_download.calls == 2


@pytest.mark.asyncio
async def test_process_watchlist_item_returns_true_when_deferred():
    use_case = ProcessWatchlistItemUseCase(
        watchlist_search_query_builder=_FakeBuildSearchQuery(),
        find_best_torrent_query=_FakeFindBestTorrent([_torrent_result()]),
        try_send_torrent_use_case=_FakeTryDownload([(False, None, True)]),
        create_active_download_use_case=_FakeCreateActiveDownload(),
        remove_watchlist_entry_use_case=_FakeRemoveWatchlist(),
        get_missing_tv_episodes_query=_FakeGetMissingTvEpisodes(),
    )

    outcome = await use_case.execute(_entry())

    assert outcome == WatchlistItemProcessOutcome.DEFERRED


@pytest.mark.asyncio
async def test_process_watchlist_item_returns_false_when_no_search_results():
    use_case = ProcessWatchlistItemUseCase(
        watchlist_search_query_builder=_FakeBuildSearchQuery(),
        find_best_torrent_query=_FakeFindBestTorrent([]),
        try_send_torrent_use_case=_FakeTryDownload([]),
        create_active_download_use_case=_FakeCreateActiveDownload(),
        remove_watchlist_entry_use_case=_FakeRemoveWatchlist(),
        get_missing_tv_episodes_query=_FakeGetMissingTvEpisodes(),
    )

    outcome = await use_case.execute(_entry())

    assert outcome == WatchlistItemProcessOutcome.NO_TORRENT


@pytest.mark.asyncio
async def test_process_show_watchlist_downloads_first_missing_episode():
    create_uc = _FakeCreateActiveDownload()
    remove_uc = _FakeRemoveWatchlist()
    find_best = _FakeFindBestTorrent([_torrent_result()])
    use_case = ProcessWatchlistItemUseCase(
        watchlist_search_query_builder=_FakeBuildSearchQuery(),
        find_best_torrent_query=find_best,
        try_send_torrent_use_case=_FakeTryDownload(
            [(True, Torrent(hash="a" * 40, file_name="Show.mkv", state="Downloading"), False)]
        ),
        create_active_download_use_case=create_uc,
        remove_watchlist_entry_use_case=remove_uc,
        get_missing_tv_episodes_query=_FakeGetMissingTvEpisodes(
            [TvEpisode(season=1, episode=2)]
        ),
    )

    outcome = await use_case.execute(
        _entry(
            title="Breaking Bad",
            guid="plex://show/1",
            type=MediaType.SHOW,
            year=2008,
        )
    )

    assert outcome == WatchlistItemProcessOutcome.SENT_TO_DELUGE
    assert find_best.calls == [("Breaking Bad S01E02", "tv")]
    assert create_uc.created[0].season == 1
    assert create_uc.created[0].episode == 2
    assert remove_uc.removed == []


@pytest.mark.asyncio
async def test_process_show_keeps_watchlist_when_buffer_empty_but_not_complete():
    remove_uc = _FakeRemoveWatchlist()
    use_case = ProcessWatchlistItemUseCase(
        watchlist_search_query_builder=_FakeBuildSearchQuery(),
        find_best_torrent_query=_FakeFindBestTorrent([]),
        try_send_torrent_use_case=_FakeTryDownload([]),
        create_active_download_use_case=_FakeCreateActiveDownload(),
        remove_watchlist_entry_use_case=remove_uc,
        get_missing_tv_episodes_query=_FakeGetMissingTvEpisodes(
            missing=[TvEpisode(season=2, episode=1)],
            download_missing=[],
        ),
    )
    outcome = await use_case.execute(
        _entry(title="Breaking Bad", guid="plex://show/1", type=MediaType.SHOW)
    )
    assert outcome == WatchlistItemProcessOutcome.NO_TORRENT
    assert remove_uc.removed == []


@pytest.mark.asyncio
async def test_process_show_watchlist_removes_when_complete():
    remove_uc = _FakeRemoveWatchlist()
    use_case = ProcessWatchlistItemUseCase(
        watchlist_search_query_builder=_FakeBuildSearchQuery(),
        find_best_torrent_query=_FakeFindBestTorrent([]),
        try_send_torrent_use_case=_FakeTryDownload([]),
        create_active_download_use_case=_FakeCreateActiveDownload(),
        remove_watchlist_entry_use_case=remove_uc,
        get_missing_tv_episodes_query=_FakeGetMissingTvEpisodes([]),
    )

    outcome = await use_case.execute(
        _entry(title="Breaking Bad", guid="plex://show/1", type=MediaType.SHOW)
    )

    assert outcome == WatchlistItemProcessOutcome.SENT_TO_DELUGE
    assert len(remove_uc.removed) == 1
    assert remove_uc.removed[0].item.rating_key == "123"
