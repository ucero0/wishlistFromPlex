"""Factory for Plex watchlist adapter."""
from app.application.plex.queries.get_watchlist_query import GetWatchlistQuery
from app.application.plex.use_cases.add_watchlist_item_use_case import AddWatchlistItemUseCase
from app.application.plex.use_cases.remove_watchlist_item_use_case import RemoveWatchlistItemUseCase
from app.composition.plex_external import (
    build_add_watchlist_item_use_case,
    build_get_watchlist_query,
    build_remove_watchlist_item_use_case,
)


def create_get_watchlist_query() -> GetWatchlistQuery:
    return build_get_watchlist_query()


def create_remove_watchlist_item_use_case() -> RemoveWatchlistItemUseCase:
    return build_remove_watchlist_item_use_case()


def create_add_watchlist_item_use_case() -> AddWatchlistItemUseCase:
    return build_add_watchlist_item_use_case()
