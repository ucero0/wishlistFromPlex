"""Tests for TV torrent title year filtering."""
from app.domain.services.tv_show_torrent_title_filter import (
    extract_tv_years_from_title,
    torrent_title_conflicts_with_show_year,
)


def test_rejects_when_title_year_does_not_match_show():
    assert torrent_title_conflicts_with_show_year(
        "Scrubs 2026 S01E02 1080p WEB-DL", 2001
    )
    assert torrent_title_conflicts_with_show_year(
        "Scrubs S01E02 2026 1080p DSNP WEB-DL", 2001
    )


def test_allows_when_title_includes_show_year():
    assert not torrent_title_conflicts_with_show_year("Scrubs 2001 S01E01", 2001)


def test_allows_when_title_has_no_year():
    assert not torrent_title_conflicts_with_show_year(
        "Scrubs.S01E01.My.First.Day.PDTV.XviD-TVEP", 2001
    )
    assert not torrent_title_conflicts_with_show_year("Breaking Bad S01E01", 2008)


def test_ignores_resolution_and_dimensions():
    assert extract_tv_years_from_title("Scrubs S01E01 1080p WEB-DL") == []
    assert extract_tv_years_from_title("Scrubs S01E01 2160p HEVC x265") == []
    assert extract_tv_years_from_title("Scrubs S01E01 1920x1080 BluRay") == []
    assert not torrent_title_conflicts_with_show_year(
        "Scrubs S01E01 1080p WEB-DL x264", 2001
    )
    assert not torrent_title_conflicts_with_show_year(
        "Scrubs S01E01 3840x2160 HEVC", 2001
    )


def test_still_detects_show_year_beside_resolution():
    assert extract_tv_years_from_title("Scrubs 2026 S01E01 1080p WEB-DL") == [2026]
    assert torrent_title_conflicts_with_show_year(
        "Scrubs 2026 S01E01 1080p WEB-DL", 2001
    )


def test_skips_filter_when_show_year_unknown():
    assert not torrent_title_conflicts_with_show_year("Scrubs 2026 S01E01", None)
