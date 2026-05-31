"""Tests for ResolvePlexLibraryIdentityQuery."""
import pytest

from app.application.plex.queries.resolve_plex_library_identity_query import (
    ResolvePlexLibraryIdentityQuery,
)
from app.domain.models.media import MediaItem, MediaType
from app.domain.models.plex_library_identity import PlexLibraryIdentity


class _FakeLibraryProvider:
    def __init__(self, tmdb_identity=None, title_identity=None):
        self._tmdb_identity = tmdb_identity
        self._title_identity = title_identity
        self.title_calls: list[tuple] = []

    async def resolve_library_identity_for_tmdb_id(self, tmdb_id, media_type):
        return self._tmdb_identity

    async def resolve_library_identity_by_title(
        self, title, media_type, *, tmdb_id=None, year=None
    ):
        self.title_calls.append((title, media_type, tmdb_id, year))
        return self._title_identity


@pytest.mark.asyncio
async def test_falls_back_to_title_search_when_tmdb_guid_lookup_misses():
    provider = _FakeLibraryProvider(
        tmdb_identity=None,
        title_identity=PlexLibraryIdentity(
            plex_guid="plex://show/fg",
            rating_key="7205",
        ),
    )
    query = ResolvePlexLibraryIdentityQuery(provider)
    media = MediaItem(
        guid="tmdb://tv/1434",
        title="Family Guy",
        year=1999,
        type=MediaType.SHOW,
    )
    identity = await query.execute(media)
    assert identity is not None
    assert identity.plex_guid == "plex://show/fg"
    assert provider.title_calls == [("Family Guy", "tv", 1434, 1999)]
