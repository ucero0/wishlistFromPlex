"""Tests for Orchestration API routes."""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timezone

from app.modules.plex.models import WishlistItem, MediaType
from app.modules.torrent_search.models import TorrentSearchResult, SearchStatus


@pytest.fixture
def sample_wishlist_items(db_session):
    """Create wishlist items for testing."""
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
    ]
    
    for item in items:
        db_session.add(item)
    db_session.commit()
    
    return items


class TestRunOrchestration:
    """Tests for POST /orchestration/run endpoint."""

    @pytest.mark.asyncio
    @patch("app.modules.orchestration.routes.OrchestrationService")
    async def test_run_orchestration_success(
        self, mock_service_class, client, sample_wishlist_items
    ):
        """Test running orchestration successfully."""
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        
        mock_result = {
            "success": True,
            "sync_summary": {
                "users_processed": 1,
                "items_fetched": 2,
                "new_items": 2,
                "updated_items": 0,
            },
            "items_processed": 2,
            "items_searched": 2,
            "items_added_to_deluge": 2,
            "errors": [],
            "run_time": datetime.now(timezone.utc).isoformat(),
            "duration_seconds": 5.5,
            "details": {"search_results": []},
        }
        mock_service.run_full_workflow = AsyncMock(return_value=mock_result)
        
        response = client.post("/orchestration/run?auto_search=true&force_research=false")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["items_searched"] == 2
        assert data["items_added_to_deluge"] == 2

    @pytest.mark.asyncio
    @patch("app.modules.orchestration.routes.OrchestrationService")
    async def test_run_orchestration_with_error(
        self, mock_service_class, client
    ):
        """Test orchestration endpoint handles errors."""
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.run_full_workflow = AsyncMock(side_effect=Exception("Test error"))
        
        response = client.post("/orchestration/run")
        
        assert response.status_code == 500
        assert "Test error" in response.json()["detail"]


class TestProcessNewItems:
    """Tests for POST /orchestration/process-new endpoint."""

    @pytest.mark.asyncio
    @patch("app.modules.orchestration.routes.OrchestrationService")
    async def test_process_new_items_success(
        self, mock_service_class, client
    ):
        """Test processing new items successfully."""
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        
        mock_result = {
            "success": True,
            "sync_summary": {"new_items": 1},
            "items_processed": 1,
            "items_searched": 1,
            "items_added_to_deluge": 1,
            "errors": [],
            "run_time": datetime.now(timezone.utc).isoformat(),
            "details": {},
        }
        mock_service.process_new_items_only = AsyncMock(return_value=mock_result)
        
        response = client.post("/orchestration/process-new")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["items_processed"] == 1


class TestGetStats:
    """Tests for GET /orchestration/stats endpoint."""

    def test_get_stats_success(self, client):
        """Test getting orchestration stats."""
        with patch("app.modules.orchestration.routes.OrchestrationService") as mock_service_class:
            mock_service = MagicMock()
            mock_service_class.return_value = mock_service
            
            mock_stats = {
                "search_stats": {
                    "total_searches": 10,
                    "added": 5,
                },
                "total_wishlist_items": 15,
                "items_with_searches": 10,
                "items_pending_search": 5,
            }
            mock_service.get_stats.return_value = mock_stats
            
            response = client.get("/orchestration/stats")
            
            assert response.status_code == 200
            data = response.json()
            assert data["total_runs"] == 10
            assert data["total_items_processed"] == 15
            assert data["total_items_added"] == 5


class TestGetPendingItems:
    """Tests for GET /orchestration/pending endpoint."""

    def test_get_pending_items(self, client, sample_wishlist_items, db_session):
        """Test getting pending items."""
        # Create a search result for one item
        search_result = TorrentSearchResult(
            rating_key="rating_key_1",
            status=SearchStatus.ADDED,
            searched_at=datetime.now(timezone.utc),
        )
        db_session.add(search_result)
        db_session.commit()
        
        response = client.get("/orchestration/pending")
        
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1  # Only rating_key_2 should be pending
        assert len(data["items"]) == 1
        assert data["items"][0]["rating_key"] == "rating_key_2"

    def test_get_pending_items_empty(self, client, db_session):
        """Test getting pending items when none exist."""
        # Create items but all have search results
        item = WishlistItem(
            guid="plex://movie/test",
            rating_key="test_key",
            title="Test Movie",
            added_at=datetime.now(timezone.utc),
            last_seen_at=datetime.now(timezone.utc),
        )
        db_session.add(item)
        
        search_result = TorrentSearchResult(
            rating_key="test_key",
            status=SearchStatus.ADDED,
            searched_at=datetime.now(timezone.utc),
        )
        db_session.add(search_result)
        db_session.commit()
        
        response = client.get("/orchestration/pending")
        
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
        assert len(data["items"]) == 0

