"""
Live integration tests for Plex API.

These tests require a real Plex token and are SKIPPED by default.

To run these tests:
    PLEX_TEST_TOKEN=your_token pytest tests/integration/test_plex_live.py -v

WARNING: Some tests may modify your watchlist!
"""
import os
import pytest
from unittest.mock import MagicMock

# Skip all tests in this module if no token is provided
PLEX_TOKEN = os.environ.get("PLEX_TEST_TOKEN")
pytestmark = pytest.mark.skipif(
    not PLEX_TOKEN,
    reason="PLEX_TEST_TOKEN environment variable not set"
)


class TestPlexAccountLive:
    """Live tests for Plex account functionality."""

    def test_account_connection(self):
        """Test connecting to Plex with real token."""
        from plexapi.myplex import MyPlexAccount
        
        account = MyPlexAccount(token=PLEX_TOKEN)
        
        assert account is not None
        assert account.username is not None
        assert account.uuid is not None
        print(f"\n✅ Connected as: {account.username}")

    def test_get_account_info(self):
        """Test getting account info via our service."""
        from app.modules.plex.service import get_account_info
        import asyncio
        
        info = asyncio.run(get_account_info(PLEX_TOKEN))
        
        assert info is not None
        assert info.username is not None
        assert info.uuid is not None
        print(f"\n✅ Account: {info.username} ({info.email})")


class TestPlexWatchlistLive:
    """Live tests for Plex watchlist functionality."""

    @pytest.mark.asyncio
    async def test_get_watchlist(self):
        """Test fetching watchlist with real token."""
        from app.modules.plex.service import get_watchlist
        
        items = await get_watchlist(PLEX_TOKEN)
        
        assert isinstance(items, list)
        print(f"\n✅ Found {len(items)} items in watchlist")
        
        if items:
            item = items[0]
            print(f"   First item: {item.title}")
            assert item.guid is not None
            assert item.title is not None

    @pytest.mark.asyncio
    async def test_watchlist_item_structure(self):
        """Test that watchlist items have expected fields."""
        from app.modules.plex.service import get_watchlist
        
        items = await get_watchlist(PLEX_TOKEN)
        
        if not items:
            pytest.skip("Watchlist is empty")
        
        item = items[0]
        
        # Required fields
        assert item.guid is not None
        assert item.title is not None
        
        # Optional fields should be accessible
        print(f"\n   GUID: {item.guid}")
        print(f"   Title: {item.title}")
        print(f"   Year: {item.year}")
        print(f"   Type: {item.media_type}")
        print(f"   Rating Key: {item.rating_key}")


class TestPlexSearchLive:
    """Live tests for Plex search functionality."""

    @pytest.mark.asyncio
    async def test_search_movies(self):
        """Test searching for movies."""
        from app.modules.plex.service import search_plex
        
        results = await search_plex(PLEX_TOKEN, "Inception", limit=5)
        
        assert isinstance(results, list)
        print(f"\n✅ Found {len(results)} results for 'Inception'")
        
        # Should find at least one result
        assert len(results) > 0
        
        for item in results:
            print(f"   - {item.title} ({item.year})")

    @pytest.mark.asyncio
    async def test_search_shows(self):
        """Test searching for TV shows."""
        from app.modules.plex.service import search_plex
        
        results = await search_plex(PLEX_TOKEN, "Breaking Bad", limit=5)
        
        assert isinstance(results, list)
        assert len(results) > 0
        print(f"\n✅ Found {len(results)} results for 'Breaking Bad'")


class TestPlexServerLive:
    """Live tests for Plex server functionality."""

    def test_list_servers(self):
        """Test listing available servers."""
        from plexapi.myplex import MyPlexAccount
        
        account = MyPlexAccount(token=PLEX_TOKEN)
        resources = account.resources()
        servers = [r for r in resources if r.provides == "server"]
        
        print(f"\n✅ Found {len(servers)} server(s)")
        for server in servers:
            print(f"   - {server.name} (owned: {server.owned})")

    def test_connect_to_server(self):
        """Test connecting to the first available server."""
        from plexapi.myplex import MyPlexAccount
        
        account = MyPlexAccount(token=PLEX_TOKEN)
        resources = account.resources()
        servers = [r for r in resources if r.provides == "server" and r.owned]
        
        if not servers:
            pytest.skip("No owned servers found")
        
        server = servers[0]
        
        try:
            plex = server.connect()
            print(f"\n✅ Connected to server: {server.name}")
            print(f"   Library sections: {len(plex.library.sections())}")
            
            for section in plex.library.sections():
                print(f"   - {section.title} ({section.type})")
                
        except Exception as e:
            pytest.skip(f"Could not connect to server: {e}")


# These tests MODIFY your watchlist - disabled by default
class TestPlexWatchlistModifyLive:
    """
    Live tests that modify watchlist.
    
    DANGEROUS: These tests will add/remove items from your watchlist!
    Only run if you understand the implications.
    
    To enable:
        PLEX_TEST_TOKEN=token PLEX_TEST_MODIFY=1 pytest tests/integration/test_plex_live.py::TestPlexWatchlistModifyLive -v
    """

    @pytest.fixture(autouse=True)
    def check_modify_enabled(self):
        """Skip unless PLEX_TEST_MODIFY is set."""
        if not os.environ.get("PLEX_TEST_MODIFY"):
            pytest.skip("PLEX_TEST_MODIFY not set - skipping destructive tests")

    @pytest.mark.asyncio
    async def test_add_and_remove_from_watchlist(self):
        """Test adding and removing an item from watchlist."""
        from app.modules.plex.service import (
            add_to_watchlist,
            remove_from_watchlist,
            search_plex,
        )
        
        # Search for a known movie
        results = await search_plex(PLEX_TOKEN, "The Matrix 1999", limit=1)
        
        if not results:
            pytest.skip("Could not find test movie")
        
        test_guid = results[0].guid
        print(f"\n   Testing with: {results[0].title} ({test_guid})")
        
        # Add to watchlist
        add_result = await add_to_watchlist(PLEX_TOKEN, test_guid)
        print(f"   Add result: {add_result}")
        
        # Remove from watchlist
        remove_result = await remove_from_watchlist(PLEX_TOKEN, test_guid)
        print(f"   Remove result: {remove_result}")
        
        # At least one should succeed
        assert add_result or remove_result, "Both add and remove failed"

