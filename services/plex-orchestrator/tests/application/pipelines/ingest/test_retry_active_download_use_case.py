"""Tests for RetryActiveDownloadUseCase."""
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.pipelines.ingest.models.retry_active_download_outcome import (
    RetryActiveDownloadOutcome,
)
from app.application.pipelines.ingest.use_cases.retry_active_download_use_case import (
    RetryActiveDownloadUseCase,
)
from app.domain.models.active_download import ActiveDownload
from app.domain.models.torrent import Torrent
from app.domain.models.torrent_search import QualityInfo, TorrentSearchResult


def _active(**kwargs) -> ActiveDownload:
    defaults = dict(
        id=1,
        plex_guid="plex://movie/1",
        prowlarr_guid="old-guid",
        uid="a" * 40,
        title="Dune",
        year=2021,
        type="movie",
    )
    defaults.update(kwargs)
    return ActiveDownload(**defaults)


def _torrent_result(guid="new-guid"):
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


def _use_case(**overrides):
    find_best = AsyncMock()
    find_best.execute = AsyncMock(return_value=overrides.pop("torrent_results", []))
    is_blacklisted = AsyncMock()
    is_blacklisted.execute = AsyncMock(
        return_value=overrides.pop("blacklisted", False)
    )
    space_checker = MagicMock()
    space_checker.has_space_for_torrent.return_value = overrides.pop(
        "has_space", (True, None, None)
    )
    enqueue = AsyncMock()
    enqueue.execute = AsyncMock()
    send = AsyncMock()
    send.execute = AsyncMock(return_value=overrides.pop("sent_torrent", None))
    update = AsyncMock()
    update.execute = AsyncMock()
    blacklist = AsyncMock()
    blacklist.execute = AsyncMock()
    deluge = AsyncMock()
    deluge.remove_torrent = AsyncMock()
    builder = overrides.pop("search_builder", None)
    return (
        RetryActiveDownloadUseCase(
            find_best_torrent_query=find_best,
            is_blacklisted_query=is_blacklisted,
            download_volume_space_checker=space_checker,
            enqueue_deferred_use_case=enqueue,
            send_torrent_to_deluge_service=send,
            update_active_download_use_case=update,
            add_torrent_to_blacklist_use_case=blacklist,
            deluge_provider=deluge,
            watchlist_search_query_builder=builder,
        ),
        find_best,
        is_blacklisted,
        enqueue,
        send,
        update,
        blacklist,
        deluge,
    )


@pytest.mark.asyncio
async def test_retry_updates_active_download_on_success():
    sent = Torrent(hash="b" * 40, file_name="dune.mkv", state="downloading")
    use_case, find_best, _, _, send, update, _, _ = _use_case(
        torrent_results=[_torrent_result()],
        sent_torrent=sent,
    )

    outcome = await use_case.execute(_active())

    assert outcome == RetryActiveDownloadOutcome.SUCCESS
    find_best.execute.assert_awaited_once_with(
        "Dune 2021", media_type="movie", show_year=None
    )
    send.execute.assert_awaited_once()
    update.execute.assert_awaited_once()
    updated = update.execute.await_args.args[0]
    assert updated.prowlarr_guid == "new-guid"
    assert updated.uid == "b" * 40
    assert updated.file_name == "dune.mkv"
    assert updated.id == 1


@pytest.mark.asyncio
async def test_retry_skips_blacklisted_and_tries_next():
    sent = Torrent(hash="c" * 40, file_name="dune2.mkv", state="downloading")
    use_case, _, is_blacklisted, _, send, update, _, _ = _use_case(
        torrent_results=[_torrent_result("bad-guid"), _torrent_result("good-guid")],
        sent_torrent=sent,
    )
    is_blacklisted.execute = AsyncMock(side_effect=[True, False])

    outcome = await use_case.execute(_active())

    assert outcome == RetryActiveDownloadOutcome.SUCCESS
    assert is_blacklisted.execute.await_count == 2
    send.execute.assert_awaited_once()
    assert update.execute.await_args.args[0].prowlarr_guid == "good-guid"


@pytest.mark.asyncio
async def test_retry_defers_when_volume_full():
    use_case, _, _, enqueue, send, update, _, _ = _use_case(
        torrent_results=[_torrent_result()],
        has_space=(False, "full", None),
    )

    outcome = await use_case.execute(_active())

    assert outcome == RetryActiveDownloadOutcome.DEFERRED
    enqueue.execute.assert_awaited_once()
    send.execute.assert_not_awaited()
    update.execute.assert_not_awaited()


@pytest.mark.asyncio
async def test_retry_returns_no_torrent_when_search_empty():
    use_case, _, _, _, _, _, _, _ = _use_case(torrent_results=[])

    outcome = await use_case.execute(_active())

    assert outcome == RetryActiveDownloadOutcome.NO_TORRENT


@pytest.mark.asyncio
async def test_retry_tv_uses_episode_search_queries():
    builder = MagicMock()
    builder.build_tv_episode_search_queries.return_value = [
        "Scrubs S01E01 Pilot",
        "Scrubs S01E01",
    ]
    use_case, find_best, _, _, _, _, _, _ = _use_case(
        torrent_results=[],
        search_builder=builder,
    )

    await use_case.execute(
        _active(
            title="Scrubs",
            type="show",
            season=1,
            episode=1,
            episode_name="Pilot",
        )
    )

    assert find_best.execute.await_count == 2
    find_best.execute.assert_any_await(
        "Scrubs S01E01 Pilot", media_type="tv", show_year=2021
    )


@pytest.mark.asyncio
async def test_retry_skips_same_infohash_via_different_guid_and_tries_next():
    removed_hash = "a" * 40
    alt_guid = f"magnet:?xt=urn:btih:{removed_hash.upper()}&dn=Same+Release"
    other_guid = "magnet:?xt=urn:btih:" + ("b" * 40) + "&dn=Other"
    sent = Torrent(hash="c" * 40, file_name="scrubs.mkv", state="downloading")
    use_case, _, is_blacklisted, _, send, update, blacklist, deluge = _use_case(
        torrent_results=[
            _torrent_result(alt_guid),
            _torrent_result(other_guid),
        ],
        sent_torrent=sent,
    )

    outcome = await use_case.execute(_active(uid=removed_hash, type="show"))

    assert outcome == RetryActiveDownloadOutcome.SUCCESS
    send.execute.assert_awaited_once()
    deluge.remove_torrent.assert_not_awaited()
    blacklist.execute.assert_awaited_once()
    assert update.execute.await_args.args[0].uid == "c" * 40


@pytest.mark.asyncio
async def test_retry_removes_torrent_when_deluge_readds_same_infohash():
    removed_hash = "a" * 40
    other_guid = "https://indexer.example/release-1"
    use_case, _, _, _, send, update, blacklist, deluge = _use_case(
        torrent_results=[_torrent_result(other_guid)],
        sent_torrent=Torrent(
            hash=removed_hash, file_name="bad.mkv", state="downloading"
        ),
    )

    outcome = await use_case.execute(_active(uid=removed_hash))

    assert outcome == RetryActiveDownloadOutcome.SEND_FAILED
    send.execute.assert_awaited_once()
    deluge.remove_torrent.assert_awaited_once_with(removed_hash, remove_data=True)
    blacklist.execute.assert_awaited_once()
    update.execute.assert_not_awaited()
