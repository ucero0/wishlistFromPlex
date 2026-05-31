"""Serialize watchlist subscribers for DB storage."""
import json

from app.domain.models.watchlist_subscriber import WatchlistSubscriber


def subscribers_to_json(subscribers: list[WatchlistSubscriber]) -> str | None:
    if not subscribers:
        return None
    return json.dumps([s.model_dump(mode="json") for s in subscribers])


def subscribers_from_json(raw: str | None) -> list[WatchlistSubscriber]:
    if not raw:
        return []
    data = json.loads(raw)
    return [WatchlistSubscriber.model_validate(row) for row in data]
