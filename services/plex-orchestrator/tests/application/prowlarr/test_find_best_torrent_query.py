"""Tests for GetBestTorrentsQuery seeder filtering."""

from app.application.prowlarr.queries.find_best_torrent_query import GetBestTorrentsQuery
from app.domain.models.torrent_search import TorrentSearchResult, QualityInfo
from app.domain.services.torrent_quality_service import TorrentQualityService


def _result(title: str, seeders: int) -> TorrentSearchResult:
    return TorrentSearchResult(
        title=title,
        guid=f"guid-{title}",
        indexerId=1,
        seeders=seeders,
        quality_score=0,
        quality_info=QualityInfo(),
    )


def test_keeps_results_with_at_least_two_seeders():
    query = GetBestTorrentsQuery(search_provider=object(), quality_service=TorrentQualityService())
    results = query._process_search_results(
        [_result("Movie 1080p WEB-DL", 5), _result("Movie 720p", 1)],
        media_type="movie",
    )
    assert len(results) == 1
    assert results[0].seeders == 5


def test_rejects_results_with_fewer_than_two_seeders():
    query = GetBestTorrentsQuery(search_provider=object(), quality_service=TorrentQualityService())
    results = query._process_search_results(
        [_result("Movie 1080p WEB-DL", 1), _result("Movie 720p", 0)],
        media_type="movie",
    )
    assert results == []


def test_returns_empty_when_no_results_pass():
    query = GetBestTorrentsQuery(search_provider=object(), quality_service=TorrentQualityService())
    results = query._process_search_results(
        [_result("Movie 1080p WEB-DL", 0)],
        media_type="movie",
    )
    assert results == []


def test_rejects_tv_result_when_show_not_before_episode():
    query = GetBestTorrentsQuery(search_provider=object(), quality_service=TorrentQualityService())
    results = query._process_search_results(
        [
            _result("Ms Marvel S01E02 1080p WEB-DL-thePunisher", 10),
            _result("The Punisher S01E02 1080p WEB-DL", 5),
        ],
        media_type="tv",
        show_title="The Punisher",
        season=1,
        episode=2,
    )
    assert len(results) == 1
    assert "The Punisher" in results[0].title
