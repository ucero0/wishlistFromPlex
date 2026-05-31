"""Map watchlist entries to persisted download tracking fields."""
from app.domain.models.active_download import ActiveDownload
from app.domain.models.deferred_download import DeferredDownload
from app.domain.models.watchlist_item_for_user import WatchlistItemForUser
from app.domain.models.watchlist_source import WatchlistSource
from app.domain.services.tmdb_guid import parse_tmdb_guid


def tmdb_media_id_from_item(entry: WatchlistItemForUser) -> int | None:
    if entry.source != WatchlistSource.TMDB:
        return None
    parsed = parse_tmdb_guid(entry.item.guid or "")
    if parsed:
        return parsed[1]
    rating_key = entry.item.rating_key
    if rating_key and rating_key.isdigit():
        return int(rating_key)
    return None


def active_download_from_watchlist_entry(
    entry: WatchlistItemForUser,
    *,
    prowlarr_guid: str,
    uid: str,
    file_name: str | None,
    season: int | None = None,
    episode: int | None = None,
    episode_name: str | None = None,
) -> ActiveDownload:
    watchlist = entry.item
    return ActiveDownload(
        plex_guid=watchlist.guid or "",
        plex_library_guid=watchlist.plex_library_guid,
        watchlist_item_id=watchlist.rating_key
        if entry.source == WatchlistSource.PLEX
        else None,
        plex_user_token=entry.user_token(),
        watchlist_source=entry.source.value,
        tmdb_media_id=tmdb_media_id_from_item(entry),
        tmdb_account_id=entry.tmdb_account_id,
        prowlarr_guid=prowlarr_guid,
        uid=uid,
        title=watchlist.title or "",
        file_name=file_name,
        year=watchlist.year,
        type=str(watchlist.type.value if hasattr(watchlist.type, "value") else watchlist.type),
        season=season,
        episode=episode,
        episode_name=episode_name,
    )


def deferred_download_from_watchlist(
    entry: WatchlistItemForUser,
    *,
    guid_prowlarr: str,
    indexer_id: int,
    torrent_title: str,
    search_query: str,
    size_bytes: int | None,
    magnet_url: str | None,
    defer_reason: str,
    season: int | None = None,
    episode: int | None = None,
    episode_name: str | None = None,
) -> DeferredDownload:
    watchlist = entry.item
    media_type = str(
        watchlist.type.value if hasattr(watchlist.type, "value") else watchlist.type
    )
    return DeferredDownload(
        guid_plex=watchlist.guid or "",
        plex_library_guid=watchlist.plex_library_guid,
        rating_key=watchlist.rating_key
        if entry.source == WatchlistSource.PLEX
        else None,
        plex_user_token=entry.user_token(),
        watchlist_source=entry.source.value,
        tmdb_media_id=tmdb_media_id_from_item(entry),
        tmdb_account_id=entry.tmdb_account_id,
        guid_prowlarr=guid_prowlarr,
        indexer_id=indexer_id,
        torrent_title=torrent_title,
        media_title=watchlist.title or "",
        year=watchlist.year,
        media_type=media_type,
        season=season,
        episode=episode,
        episode_name=episode_name,
        search_query=search_query,
        size_bytes=size_bytes,
        magnet_url=magnet_url,
        defer_reason=defer_reason,
    )
