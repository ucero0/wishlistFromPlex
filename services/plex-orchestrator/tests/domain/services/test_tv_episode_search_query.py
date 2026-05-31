"""Tests for TV episode search query formatting."""
from app.domain.services.tv_episode_search_query import (
    format_tv_episode_name_search_query,
    format_tv_episode_search_query,
    parse_season_episode,
)


def test_format_tv_episode_search_query():
    assert format_tv_episode_search_query("Breaking Bad", 1, 2) == "Breaking Bad S01E02"
    assert format_tv_episode_search_query("Scrubs", 1, 9) == "Scrubs S01E09"


def test_format_tv_episode_name_search_query():
    assert (
        format_tv_episode_name_search_query("Scrubs", 1, 1, "My First Day")
        == "Scrubs S01E01 My First Day"
    )


def test_parse_season_episode_from_search_query():
    parsed = parse_season_episode("Breaking Bad S01E02")
    assert parsed is not None
    assert parsed.season == 1
    assert parsed.episode == 2


def test_parse_season_episode_ignores_show_year():
    parsed = parse_season_episode("Scrubs 2001 S01E09")
    assert parsed is not None
    assert parsed.season == 1
    assert parsed.episode == 9
