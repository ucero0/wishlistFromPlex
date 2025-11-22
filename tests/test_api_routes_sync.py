import pytest
from unittest.mock import patch, AsyncMock
from app.models.plex_user import PlexUser


class TestSyncRoutes:
    """Tests for sync routes."""
    
    @patch("app.api.routes_sync.sync_all_users")
    async def test_trigger_sync_success(self, mock_sync, client, db_session):
        """Test triggering a successful sync."""
        # Create a user
        user = PlexUser(name="Test User", plex_token="test-token", active=True)
        db_session.add(user)
        db_session.commit()
        
        # Mock sync result
        mock_sync.return_value = {
            "users_processed": 1,
            "items_fetched": 5,
            "new_items": 3,
            "updated_items": 2,
            "total_items": 5,
            "errors": [],
            "sync_time": "2023-01-01T00:00:00",
        }
        
        response = client.post(
            "/api/sync",
            headers={"X-API-Key": "test-api-key"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["users_processed"] == 1
        assert data["items_fetched"] == 5
        assert data["new_items"] == 3
    
    def test_trigger_sync_missing_api_key(self, client):
        """Test triggering sync without API key."""
        response = client.post("/api/sync")
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    @patch("app.api.routes_sync.sync_all_users")
    async def test_trigger_sync_with_errors(self, mock_sync, client):
        """Test sync that returns errors."""
        mock_sync.side_effect = Exception("Sync failed")
        
        response = client.post(
            "/api/sync",
            headers={"X-API-Key": "test-api-key"},
        )
        
        assert response.status_code == 500
        assert "Sync failed" in response.json()["detail"]
    
    def test_get_sync_status_no_sync(self, client):
        """Test getting sync status when no sync has been performed."""
        # Reset the global variable by importing and resetting it
        from app.api import routes_sync
        routes_sync._last_sync_status = None
        
        response = client.get("/api/sync/status")
        
        assert response.status_code == 404
        assert "No sync has been performed" in response.json()["detail"]
    
    @pytest.mark.asyncio
    @patch("app.api.routes_sync.sync_all_users")
    async def test_get_sync_status_after_sync(self, mock_sync, client, db_session):
        """Test getting sync status after a sync."""
        user = PlexUser(name="Test User", plex_token="test-token", active=True)
        db_session.add(user)
        db_session.commit()
        
        mock_sync.return_value = {
            "users_processed": 1,
            "items_fetched": 5,
            "new_items": 3,
            "updated_items": 2,
            "total_items": 5,
            "errors": [],
            "sync_time": "2023-01-01T00:00:00",
        }
        
        # Trigger sync first
        client.post(
            "/api/sync",
            headers={"X-API-Key": "test-api-key"},
        )
        
        # Get status
        response = client.get("/api/sync/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["users_processed"] == 1
        assert "sync_time" in data

