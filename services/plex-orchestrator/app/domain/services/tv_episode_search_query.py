"""Prowlarr search strings and SxxExx parsing aligned with Plex TV ingest naming."""
import re

from app.domain.models.tv_episode import TvEpisode

_SEASON_EPISODE_RE = re.compile(r"[Ss](?P<season>\d{1,2})[Ee](?P<episode>\d{1,3})")


def format_tv_episode_search_query(
    show_title: str,
    season: int,
    episode: int,
) -> str:
    """Prowlarr search string using show title and SxxExx."""
    return f"{show_title} S{season:02d}E{episode:02d}"


def format_tv_episode_name_search_query(
    show_title: str,
    season: int,
    episode: int,
    episode_name: str,
) -> str:
    """Prowlarr search: show title, SxxExx, then episode name."""
    token = f"S{season:02d}E{episode:02d}"
    return f"{show_title} {token} {episode_name.strip()}"


def parse_season_episode(text: str) -> TvEpisode | None:
    match = _SEASON_EPISODE_RE.search(text)
    if not match:
        return None
    return TvEpisode(
        season=int(match.group("season")),
        episode=int(match.group("episode")),
    )
