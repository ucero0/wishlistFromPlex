"""Select which missing TV episodes to download based on watch progress."""
from app.domain.models.tv_episode import TvEpisode


def is_episode_watched(ep_metadata: dict) -> bool:
    if (ep_metadata.get("viewCount") or 0) > 0:
        return True
    if (ep_metadata.get("viewOffset") or 0) > 0:
        return True
    return False


def max_watched_episode(episodes: list[TvEpisode]) -> TvEpisode | None:
    if not episodes:
        return None
    return max(episodes, key=lambda ep: (ep.season, ep.episode))


def filter_missing_for_ahead_buffer(
    catalog: list[TvEpisode],
    missing: list[TvEpisode],
    latest_watched: TvEpisode | None,
    *,
    ahead_episodes: int,
) -> list[TvEpisode]:
    """
    When nobody has watched the show, download missing episodes from the start.

    When any user has progress, only download missing episodes in the window
    immediately after the furthest watched episode (up to ``ahead_episodes``).
    """
    if not missing:
        return []

    if latest_watched is None:
        return missing[:ahead_episodes]

    catalog_keys = [ep for ep in catalog]
    try:
        latest_index = next(
            i
            for i, ep in enumerate(catalog_keys)
            if ep.season == latest_watched.season
            and ep.episode == latest_watched.episode
        )
    except StopIteration:
        return missing

    window = set(
        catalog_keys[latest_index + 1 : latest_index + 1 + ahead_episodes]
    )
    if not window:
        return []

    return [ep for ep in missing if ep in window]
