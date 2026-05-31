"""Build tracking context for torrents added directly in Deluge."""
import re

from app.domain.models.active_download import ActiveDownload
from app.domain.models.torrent import Torrent

MANUAL_PROWLARR_PREFIX = "manual:"
_SEASON_EPISODE_RE = re.compile(r"[Ss](?P<season>\d{1,2})[Ee](?P<episode>\d{1,2})")


def normalize_torrent_hash(value: str) -> str:
    return (value or "").strip().lower()


def manual_prowlarr_guid(torrent_hash: str) -> str:
    return f"{MANUAL_PROWLARR_PREFIX}{normalize_torrent_hash(torrent_hash)}"


def is_manual_active_download(active: ActiveDownload) -> bool:
    return (active.prowlarr_guid or "").startswith(MANUAL_PROWLARR_PREFIX)


def parse_season_episode(name: str) -> tuple[int, int] | None:
    match = _SEASON_EPISODE_RE.search(name or "")
    if not match:
        return None
    return int(match.group("season")), int(match.group("episode"))


def infer_media_type(name: str) -> str:
    if parse_season_episode(name):
        return "show"
    return "movie"


def infer_title(name: str) -> str:
    base = (name or "").strip()
    if not base:
        return "Manual torrent"
    for separator in ("/", "\\"):
        if separator in base:
            base = base.split(separator)[0]
    if base.lower().endswith(".torrent"):
        base = base[:-8]
    return base.strip() or "Manual torrent"


def active_download_from_deluge_torrent(
    torrent: Torrent,
    *,
    media_type: str | None = None,
    title: str | None = None,
    year: int | None = None,
) -> ActiveDownload:
    file_name = torrent.file_name or ""
    resolved_type = (media_type or infer_media_type(file_name)).lower()
    if resolved_type in ("tv", "tvshow"):
        resolved_type = "show"
    resolved_title = title or infer_title(file_name)
    season: int | None = None
    episode: int | None = None
    if resolved_type == "show":
        parsed = parse_season_episode(file_name)
        if parsed:
            season, episode = parsed
    torrent_hash = normalize_torrent_hash(torrent.hash)
    return ActiveDownload(
        plex_guid=f"manual://torrent/{torrent_hash}",
        prowlarr_guid=manual_prowlarr_guid(torrent_hash),
        uid=torrent_hash,
        title=resolved_title,
        file_name=file_name or None,
        year=year,
        type=resolved_type,
        season=season,
        episode=episode,
    )
