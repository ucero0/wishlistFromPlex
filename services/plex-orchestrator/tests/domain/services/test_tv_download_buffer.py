"""Tests for TV ahead-buffer selection."""
from app.domain.models.tv_episode import TvEpisode
from app.domain.services.tv_download_buffer import (
    filter_missing_for_ahead_buffer,
    is_episode_watched,
    max_watched_episode,
)


def test_is_episode_watched_view_count():
    assert is_episode_watched({"viewCount": 1}) is True
    assert is_episode_watched({"viewOffset": 1000}) is True
    assert is_episode_watched({"viewCount": 0, "viewOffset": 0}) is False


def test_max_watched_episode():
    eps = [TvEpisode(season=1, episode=1), TvEpisode(season=1, episode=5)]
    assert max_watched_episode(eps) == TvEpisode(season=1, episode=5)


def test_filter_missing_starts_from_beginning_when_unwatched():
    catalog = [TvEpisode(season=1, episode=i) for i in range(1, 6)]
    missing = catalog[:3]
    assert filter_missing_for_ahead_buffer(catalog, missing, None, ahead_episodes=10) == missing


def test_filter_missing_caps_at_ahead_when_unwatched():
    catalog = [TvEpisode(season=1, episode=i) for i in range(1, 21)]
    missing = catalog.copy()
    assert filter_missing_for_ahead_buffer(
        catalog, missing, None, ahead_episodes=10
    ) == catalog[:10]


def test_filter_missing_only_in_ahead_window():
    catalog = [TvEpisode(season=1, episode=i) for i in range(1, 21)]
    missing = catalog.copy()
    latest = TvEpisode(season=1, episode=5)
    result = filter_missing_for_ahead_buffer(
        catalog, missing, latest, ahead_episodes=10
    )
    assert result == catalog[5:15]
