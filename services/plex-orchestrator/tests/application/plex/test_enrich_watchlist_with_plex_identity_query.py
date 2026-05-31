import pytest

from app.application.plex.queries.enrich_watchlist_with_plex_identity_query import (
    EnrichWatchlistWithPlexIdentityQuery,
)
from app.domain.models.media import MediaItem, MediaType
from app.domain.models.plex_library_identity import PlexLibraryIdentity
from app.domain.models.watchlist_item_for_user import WatchlistItemForUser
from app.domain.models.watchlist_source import WatchlistSource


class _FakeResolveIdentity:
    async def execute(self, media: MediaItem):
        if media.guid == "tmdb://tv/1434":
            return PlexLibraryIdentity(
                plex_guid="plex://show/family-guy",
                rating_key="999",
            )
        return None


@pytest.mark.asyncio
async def test_enrich_tmdb_watchlist_item_with_plex_library_guid():
    query = EnrichWatchlistWithPlexIdentityQuery(_FakeResolveIdentity())
    entry = WatchlistItemForUser(
        item=MediaItem(
            guid="tmdb://tv/1434",
            title="Family Guy",
            type=MediaType.SHOW,
            rating_key="1434",
        ),
        source=WatchlistSource.TMDB,
        tmdb_account_id=1,
        tmdb_access_token="token",
    )
    enriched = await query.execute([entry])
    assert enriched[0].item.plex_library_guid == "plex://show/family-guy"
    assert enriched[0].item.guid == "tmdb://tv/1434"


@pytest.mark.asyncio
async def test_enrich_plex_watchlist_sets_plex_library_guid_from_guid():
    query = EnrichWatchlistWithPlexIdentityQuery(_FakeResolveIdentity())
    entry = WatchlistItemForUser(
        item=MediaItem(
            guid="plex://show/abc",
            rating_key="123",
            title="Scrubs",
            type=MediaType.SHOW,
        ),
        source=WatchlistSource.PLEX,
        plex_user_token="plex-token",
    )
    enriched = await query.execute([entry])
    assert enriched[0].item.plex_library_guid == "plex://show/abc"
