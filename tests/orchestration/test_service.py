"""Tests for Orchestration service layer with mocked dependencies."""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timezone

from app.modules.orchestration.service import OrchestrationService
from app.modules.plex.models import WishlistItem, MediaType, PlexUser
from app.modules.torrent_search.models import TorrentSearchResult, SearchStatus


@pytest.fixture
def orchestration_service(db_session):
    """Create an orchestration service with test database."""
    return OrchestrationService(db_session)


@pytest.fixture
def sample_wishlist_items(db_session):
    """Create multiple wishlist items for testing."""
    items = [
        WishlistItem(
            guid="plex://movie/test1",
            rating_key="rating_key_1",
            title="The Matrix",
            year=1999,
            media_type=MediaType.MOVIE,
            added_at=datetime.now(timezone.utc),
            last_seen_at=datetime.now(timezone.utc),
        ),
        WishlistItem(
            guid="plex://movie/test2",
            rating_key="rating_key_2",
            title="Inception",
            year=2010,
            media_type=MediaType.MOVIE,
            added_at=datetime.now(timezone.utc),
            last_seen_at=datetime.now(timezone.utc),
        ),
        WishlistItem(
            guid="plex://show/test3",
            rating_key="rating_key_3",
            title="Breaking Bad",
            year=2008,
            media_type=MediaType.SHOW,
            added_at=datetime.now(timezone.utc),
            last_seen_at=datetime.now(timezone.utc),
        ),
    ]
    
    for item in items:
        db_session.add(item)
    db_session.commit()
    
    for item in items:
        db_session.refresh(item)
    
    return items


@pytest.fixture
def sample_user(db_session):
    """Create a sample Plex user."""
    user = PlexUser(
        name="TestUser",
        plex_token="test-token",
        active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


class TestGetItemsToSearch:
    """Tests for _get_items_to_search method."""

    def test_get_items_without_existing_searches(
        self, orchestration_service, sample_wishlist_items, db_session
    ):
        """Test getting items that don't have search results."""
        items = orchestration_service._get_items_to_search(force_research=False)
        
        # All items should be returned since none have search results
        assert len(items) == 3
        rating_keys = {item.rating_key for item in items}
        assert rating_keys == {"rating_key_1", "rating_key_2", "rating_key_3"}

    def test_get_items_with_existing_searches(
        self, orchestration_service, sample_wishlist_items, db_session
    ):
        """Test that items with successful searches are excluded."""
        # Create a search result for one item
        search_result = TorrentSearchResult(
            rating_key="rating_key_1",
            status=SearchStatus.ADDED,
            searched_at=datetime.now(timezone.utc),
        )
        db_session.add(search_result)
        db_session.commit()
        
        items = orchestration_service._get_items_to_search(force_research=False)
        
        # Only items without successful searches should be returned
        assert len(items) == 2
        rating_keys = {item.rating_key for item in items}
        assert "rating_key_1" not in rating_keys
        assert "rating_key_2" in rating_keys
        assert "rating_key_3" in rating_keys

    def test_get_items_with_force_research(
        self, orchestration_service, sample_wishlist_items, db_session
    ):
        """Test that force_research includes all items."""
        # Create search results for all items
        for rating_key in ["rating_key_1", "rating_key_2", "rating_key_3"]:
            search_result = TorrentSearchResult(
                rating_key=rating_key,
                status=SearchStatus.ADDED,
                searched_at=datetime.now(timezone.utc),
            )
            db_session.add(search_result)
        db_session.commit()
        
        items = orchestration_service._get_items_to_search(force_research=True)
        
        # All items should be returned when force_research=True
        assert len(items) == 3

    def test_get_items_filters_out_items_without_rating_key(
        self, orchestration_service, db_session
    ):
        """Test that items without rating_key are excluded."""
        # Create item without rating_key
        item_no_key = WishlistItem(
            guid="plex://movie/no_key",
            rating_key=None,
            title="No Key Item",
            added_at=datetime.now(timezone.utc),
            last_seen_at=datetime.now(timezone.utc),
        )
        db_session.add(item_no_key)
        
        # Create item with empty rating_key
        item_empty_key = WishlistItem(
            guid="plex://movie/empty_key",
            rating_key="",
            title="Empty Key Item",
            added_at=datetime.now(timezone.utc),
            last_seen_at=datetime.now(timezone.utc),
        )
        db_session.add(item_empty_key)
        
        # Create item with valid rating_key
        item_valid = WishlistItem(
            guid="plex://movie/valid",
            rating_key="valid_key",
            title="Valid Item",
            added_at=datetime.now(timezone.utc),
            last_seen_at=datetime.now(timezone.utc),
        )
        db_session.add(item_valid)
        db_session.commit()
        
        items = orchestration_service._get_items_to_search(force_research=False)
        
        # Only item with valid rating_key should be returned
        assert len(items) == 1
        assert items[0].rating_key == "valid_key"


class TestRunFullWorkflow:
    """Tests for run_full_workflow method."""

    @pytest.mark.asyncio
    @patch("app.modules.orchestration.service.sync_all_users")
    async def test_run_workflow_with_auto_search(
        self, mock_sync, orchestration_service, sample_wishlist_items, db_session
    ):
        """Test running full workflow with auto_search enabled."""
        # Mock sync result
        mock_sync.return_value = {
            "users_processed": 1,
            "items_fetched": 3,
            "new_items": 3,
            "updated_items": 0,
            "total_items": 3,
            "errors": [],
        }
        
        # Mock search_by_query to return successful results
        with patch.object(
            orchestration_service.torrent_search_service,
            "search_by_query",
            new_callable=AsyncMock
        ) as mock_search:
            mock_search_result = MagicMock()
            mock_search_result.status = SearchStatus.ADDED
            mock_search_result.selected_torrent_title = "The Matrix 1999 2160p"
            mock_search_result.selected_torrent_quality_score = 250
            mock_search_result.torrent_hash = "abc123"
            mock_search.return_value = mock_search_result
            
            result = await orchestration_service.run_full_workflow(
                auto_search=True,
                force_research=False
            )
        
        # Verify sync was called
        mock_sync.assert_called_once_with(db_session)
        
        # Verify search was called for each item
        assert mock_search.call_count == 3
        
        # Verify result structure
        assert result["success"] is True
        assert result["items_processed"] == 3
        assert result["items_searched"] == 3
        assert result["items_added_to_deluge"] == 3
        assert len(result["errors"]) == 0
        assert "sync_summary" in result
        assert "details" in result

    @pytest.mark.asyncio
    @patch("app.modules.orchestration.service.sync_all_users")
    async def test_run_workflow_without_auto_search(
        self, mock_sync, orchestration_service, sample_wishlist_items, db_session
    ):
        """Test running workflow with auto_search disabled."""
        mock_sync.return_value = {
            "users_processed": 1,
            "items_fetched": 3,
            "new_items": 3,
            "updated_items": 0,
            "total_items": 3,
            "errors": [],
        }
        
        with patch.object(
            orchestration_service.torrent_search_service,
            "search_by_query",
            new_callable=AsyncMock
        ) as mock_search:
            result = await orchestration_service.run_full_workflow(
                auto_search=False,
                force_research=False
            )
        
        # Verify sync was called
        mock_sync.assert_called_once()
        
        # Verify search was NOT called
        mock_search.assert_not_called()
        
        # Verify result
        assert result["items_processed"] == 3
        assert result["items_searched"] == 0
        assert result["items_added_to_deluge"] == 0

    @pytest.mark.asyncio
    @patch("app.modules.orchestration.service.sync_all_users")
    async def test_run_workflow_with_sync_error(
        self, mock_sync, orchestration_service, sample_wishlist_items, db_session
    ):
        """Test workflow handles sync errors gracefully."""
        mock_sync.side_effect = Exception("Sync failed")
        
        result = await orchestration_service.run_full_workflow(
            auto_search=True,
            force_research=False
        )
        
        # Verify error was captured
        assert result["success"] is False
        assert len(result["errors"]) > 0
        assert "Sync failed" in result["errors"][0]
        assert result["sync_summary"]["users_processed"] == 0

    @pytest.mark.asyncio
    @patch("app.modules.orchestration.service.sync_all_users")
    async def test_run_workflow_with_search_errors(
        self, mock_sync, orchestration_service, sample_wishlist_items, db_session
    ):
        """Test workflow handles search errors gracefully."""
        mock_sync.return_value = {
            "users_processed": 1,
            "items_fetched": 3,
            "new_items": 3,
            "updated_items": 0,
            "total_items": 3,
            "errors": [],
        }
        
        with patch.object(
            orchestration_service.torrent_search_service,
            "search_by_query",
            new_callable=AsyncMock
        ) as mock_search:
            # First search succeeds, second fails, third succeeds
            mock_search_results = [
                MagicMock(status=SearchStatus.ADDED, torrent_hash="hash1"),
                Exception("Search failed"),
                MagicMock(status=SearchStatus.NOT_FOUND),
            ]
            mock_search.side_effect = mock_search_results
            
            result = await orchestration_service.run_full_workflow(
                auto_search=True,
                force_research=False
            )
        
        # Verify errors were captured
        assert len(result["errors"]) == 1
        assert "Search failed" in result["errors"][0]
        
        # Verify partial success
        assert result["items_searched"] == 3
        assert result["items_added_to_deluge"] == 1

    @pytest.mark.asyncio
    @patch("app.modules.orchestration.service.sync_all_users")
    async def test_run_workflow_with_different_search_statuses(
        self, mock_sync, orchestration_service, sample_wishlist_items, db_session
    ):
        """Test workflow handles different search statuses correctly."""
        mock_sync.return_value = {
            "users_processed": 1,
            "items_fetched": 3,
            "new_items": 3,
            "updated_items": 0,
            "total_items": 3,
            "errors": [],
        }
        
        with patch.object(
            orchestration_service.torrent_search_service,
            "search_by_query",
            new_callable=AsyncMock
        ) as mock_search:
            # Return different statuses
            mock_results = [
                MagicMock(
                    status=SearchStatus.ADDED,
                    selected_torrent_title="Torrent 1",
                    torrent_hash="hash1"
                ),
                MagicMock(
                    status=SearchStatus.FOUND,
                    selected_torrent_title="Torrent 2",
                    torrent_hash=None
                ),
                MagicMock(
                    status=SearchStatus.NOT_FOUND,
                    selected_torrent_title=None,
                    torrent_hash=None
                ),
            ]
            mock_search.side_effect = mock_results
            
            result = await orchestration_service.run_full_workflow(
                auto_search=True,
                force_research=False
            )
        
        # Verify counts
        assert result["items_searched"] == 3
        assert result["items_added_to_deluge"] == 1  # Only ADDED status counts
        assert len(result["errors"]) == 0


class TestProcessNewItemsOnly:
    """Tests for process_new_items_only method."""

    @pytest.mark.asyncio
    @patch("app.modules.orchestration.service.sync_all_users")
    async def test_process_new_items(
        self, mock_sync, orchestration_service, db_session
    ):
        """Test processing only newly added items."""
        # Create an old item
        old_item = WishlistItem(
            guid="plex://movie/old",
            rating_key="old_key",
            title="Old Movie",
            added_at=datetime(2020, 1, 1, tzinfo=timezone.utc),
            last_seen_at=datetime.now(timezone.utc),
        )
        db_session.add(old_item)
        
        # Create a new item (added recently)
        new_item = WishlistItem(
            guid="plex://movie/new",
            rating_key="new_key",
            title="New Movie",
            added_at=datetime.now(timezone.utc),
            last_seen_at=datetime.now(timezone.utc),
        )
        db_session.add(new_item)
        db_session.commit()
        
        mock_sync.return_value = {
            "users_processed": 1,
            "items_fetched": 2,
            "new_items": 1,
            "updated_items": 0,
            "total_items": 2,
            "errors": [],
        }
        
        with patch.object(
            orchestration_service.torrent_search_service,
            "search_by_query",
            new_callable=AsyncMock
        ) as mock_search:
            mock_search_result = MagicMock()
            mock_search_result.status = SearchStatus.ADDED
            mock_search_result.torrent_hash = "hash123"
            mock_search.return_value = mock_search_result
            
            result = await orchestration_service.process_new_items_only()
        
        # Verify only new item was processed
        assert result["items_processed"] == 1
        assert result["items_searched"] == 1
        assert mock_search.call_count == 1
        # Verify it was called with query, media_type, and rating_key
        call_args = mock_search.call_args
        assert call_args.kwargs["query"] == "New Movie"
        assert call_args.kwargs["media_type"] == "movie"
        assert call_args.kwargs["rating_key"] == "new_key"


class TestGetStats:
    """Tests for get_stats method."""

    def test_get_stats(
        self, orchestration_service, sample_wishlist_items, db_session
    ):
        """Test getting orchestration statistics."""
        # Create some search results
        search_result1 = TorrentSearchResult(
            rating_key="rating_key_1",
            status=SearchStatus.ADDED,
            searched_at=datetime.now(timezone.utc),
        )
        search_result2 = TorrentSearchResult(
            rating_key="rating_key_2",
            status=SearchStatus.NOT_FOUND,
            searched_at=datetime.now(timezone.utc),
        )
        db_session.add(search_result1)
        db_session.add(search_result2)
        db_session.commit()
        
        stats = orchestration_service.get_stats()
        
        # Verify stats structure
        assert "search_stats" in stats
        assert "items_pending_search" in stats
        assert "total_wishlist_items" in stats
        assert "items_with_searches" in stats
        
        # Verify counts
        assert stats["total_wishlist_items"] == 3
        assert stats["items_with_searches"] == 2
        assert stats["items_pending_search"] == 1  # rating_key_3 has no search

