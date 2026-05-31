"""Merge per-user watchlist rows into one item with all subscribers."""
from app.domain.models.media import MediaItem
from app.domain.models.watchlist_item_for_user import WatchlistItemForUser
from app.domain.models.watchlist_subscriber import WatchlistSubscriber
from app.domain.services.watchlist_media_identity import media_identity_key


def dedupe_subscribers(
    subscribers: list[WatchlistSubscriber],
) -> list[WatchlistSubscriber]:
    seen: set[tuple[str, int | None, int | None]] = set()
    unique: list[WatchlistSubscriber] = []
    for subscriber in subscribers:
        key = subscriber.dedupe_key()
        if key in seen:
            continue
        seen.add(key)
        unique.append(subscriber)
    return unique


def _best_item(members: list[WatchlistItemForUser]) -> MediaItem:
    for member in members:
        if member.item.plex_library_guid:
            return member.item
    return members[0].item


def group_watchlist_entries(
    entries: list[WatchlistItemForUser],
) -> list[WatchlistItemForUser]:
    buckets: dict[str, list[WatchlistItemForUser]] = {}
    for entry in entries:
        key = media_identity_key(entry.item)
        buckets.setdefault(key, []).append(entry)

    grouped: list[WatchlistItemForUser] = []
    for members in buckets.values():
        subscribers = dedupe_subscribers(
            [subscriber for member in members for subscriber in member.all_subscribers()]
        )
        if not subscribers:
            continue
        item = _best_item(members)
        plex_user_token = next(
            (s.plex_user_token for s in subscribers if s.plex_user_token),
            members[0].plex_user_token,
        )
        primary = subscribers[0]
        grouped.append(
            WatchlistItemForUser(
                item=item,
                subscribers=subscribers,
                source=primary.source,
                plex_user_id=primary.plex_user_id,
                plex_user_token=plex_user_token,
                tmdb_user_id=primary.tmdb_user_id,
                tmdb_account_id=primary.tmdb_account_id,
                tmdb_access_token=primary.tmdb_access_token,
            )
        )
    return grouped
