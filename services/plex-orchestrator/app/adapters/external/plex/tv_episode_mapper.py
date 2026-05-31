"""Map Plex metadata JSON to TV episode lists."""
from app.domain.models.tv_episode import TvEpisode
from app.domain.services.tv_download_buffer import is_episode_watched


def metadata_children_to_episodes(
    response_json: dict,
    *,
    include_specials: bool = False,
) -> list[TvEpisode]:
    episodes: list[TvEpisode] = []
    for item in response_json.get("MediaContainer", {}).get("Metadata") or []:
        if item.get("type") == "season":
            season_num = item.get("index")
            if season_num is None:
                continue
            if not include_specials and int(season_num) <= 0:
                continue
            for ep in item.get("Metadata") or []:
                if ep.get("type") != "episode":
                    continue
                ep_num = ep.get("index")
                if ep_num is None:
                    continue
                episodes.append(TvEpisode(season=int(season_num), episode=int(ep_num)))
        elif item.get("type") == "episode":
            season_num = item.get("parentIndex")
            ep_num = item.get("index")
            if season_num is None or ep_num is None:
                continue
            if not include_specials and int(season_num) <= 0:
                continue
            episodes.append(TvEpisode(season=int(season_num), episode=int(ep_num)))
    return episodes


async def crawl_show_episodes_from_discover(
    client,
    rating_key: str,
    user_token: str,
    *,
    include_specials: bool = False,
) -> list[TvEpisode]:
    episodes: list[TvEpisode] = []
    seasons_json = await client.get_metadata_children_raw(rating_key, user_token)
    for season in seasons_json.get("MediaContainer", {}).get("Metadata") or []:
        if season.get("type") != "season":
            continue
        season_num = season.get("index")
        if season_num is None:
            continue
        if not include_specials and int(season_num) <= 0:
            continue
        season_key = season.get("ratingKey")
        if not season_key:
            continue
        eps_json = await client.get_metadata_children_raw(season_key, user_token)
        for ep in eps_json.get("MediaContainer", {}).get("Metadata") or []:
            if ep.get("type") != "episode":
                continue
            ep_num = ep.get("index")
            if ep_num is None:
                continue
            episodes.append(TvEpisode(season=int(season_num), episode=int(ep_num)))
    return episodes


async def crawl_show_episodes_from_server(
    client,
    show_rating_key: str,
    *,
    admin_token: str | None = None,
    include_specials: bool = False,
) -> list[TvEpisode]:
    episodes: list[TvEpisode] = []
    seasons_json = await client.get_metadata_children_raw(
        show_rating_key, admin_token=admin_token
    )
    for season in seasons_json.get("MediaContainer", {}).get("Metadata") or []:
        if season.get("type") != "season":
            continue
        season_num = season.get("index")
        if season_num is None:
            continue
        if not include_specials and int(season_num) <= 0:
            continue
        season_key = season.get("ratingKey")
        if not season_key:
            continue
        eps_json = await client.get_metadata_children_raw(
            season_key, admin_token=admin_token
        )
        for ep in eps_json.get("MediaContainer", {}).get("Metadata") or []:
            if ep.get("type") != "episode":
                continue
            ep_num = ep.get("index")
            if ep_num is None:
                continue
            episodes.append(TvEpisode(season=int(season_num), episode=int(ep_num)))
    return episodes


async def resolve_show_rating_key_from_server(
    client,
    show_guid: str,
    *,
    user_token: str | None = None,
    admin_token: str | None = None,
) -> str | None:
    response = await client.get_library_items_raw(
        show_guid,
        media_type=2,
        admin_token=admin_token,
        user_token=user_token,
    )
    mc = response.MediaContainer
    if int(mc.get("size", 0)) != 1:
        return None
    metadata = mc.get("Metadata") or []
    if not metadata or metadata[0].get("guid") != show_guid:
        return None
    rating_key = metadata[0].get("ratingKey")
    return str(rating_key) if rating_key else None


async def crawl_watched_show_episodes_from_server(
    client,
    show_rating_key: str,
    user_token: str,
    *,
    include_specials: bool = False,
) -> list[TvEpisode]:
    episodes: list[TvEpisode] = []
    seasons_json = await client.get_metadata_children_raw(
        show_rating_key, user_token=user_token
    )
    for season in seasons_json.get("MediaContainer", {}).get("Metadata") or []:
        if season.get("type") != "season":
            continue
        season_num = season.get("index")
        if season_num is None:
            continue
        if not include_specials and int(season_num) <= 0:
            continue
        season_key = season.get("ratingKey")
        if not season_key:
            continue
        eps_json = await client.get_metadata_children_raw(
            season_key, user_token=user_token
        )
        for ep in eps_json.get("MediaContainer", {}).get("Metadata") or []:
            if ep.get("type") != "episode":
                continue
            if not is_episode_watched(ep):
                continue
            ep_num = ep.get("index")
            if ep_num is None:
                continue
            episodes.append(TvEpisode(season=int(season_num), episode=int(ep_num)))
    return episodes
