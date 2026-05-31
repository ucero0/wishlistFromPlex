"""Helpers for TMDB media identifiers in watchlist/download flows."""


def build_tmdb_movie_guid(tmdb_id: int) -> str:
    return f"tmdb://movie/{tmdb_id}"


def build_tmdb_tv_guid(tmdb_id: int) -> str:
    return f"tmdb://tv/{tmdb_id}"


def parse_tmdb_guid(guid: str) -> tuple[str, int] | None:
    if not guid:
        return None
    for media_type, prefix in (("movie", "tmdb://movie/"), ("tv", "tmdb://tv/")):
        if guid.startswith(prefix):
            raw_id = guid[len(prefix) :].strip("/")
            if raw_id.isdigit():
                return media_type, int(raw_id)
    return None


def is_tmdb_guid(guid: str) -> bool:
    return parse_tmdb_guid(guid) is not None


def parse_agent_tmdb_id(guid: str) -> tuple[str, int] | None:
    """Parse Plex agent guids such as com.plexapp.agents.themoviedb://tv/1396."""
    if not guid:
        return None
    for media_type, marker in (("tv", "://tv/"), ("movie", "://movie/")):
        for agent in ("com.plexapp.agents.themoviedb", "com.plexapp.agents.tmdb"):
            needle = f"{agent}{marker}"
            idx = guid.find(needle)
            if idx < 0:
                continue
            raw_id = guid[idx + len(needle) :].split("?")[0].strip("/")
            if raw_id.isdigit():
                return media_type, int(raw_id)
    return None


def resolve_tmdb_tv_id_from_guid(guid: str) -> int | None:
    parsed = parse_tmdb_guid(guid)
    if parsed and parsed[0] == "tv":
        return parsed[1]
    agent = parse_agent_tmdb_id(guid)
    if agent and agent[0] == "tv":
        return agent[1]
    return None
