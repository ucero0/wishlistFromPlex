"""Factory for TMDB queries."""
from app.application.tmdb.queries.get_original_title_query import GetOriginalTitleFromTMDBQuery
from app.application.tmdb.queries.test_tmdb_connection_query import TestTmdbConnectionQuery
from app.composition.tmdb import (
    build_get_original_title_from_tmdb_query,
    build_test_tmdb_connection_query,
)


def create_test_tmdb_connection_query() -> TestTmdbConnectionQuery:
    return build_test_tmdb_connection_query()


def create_get_original_title_from_tmdb_query() -> GetOriginalTitleFromTMDBQuery:
    return build_get_original_title_from_tmdb_query()
