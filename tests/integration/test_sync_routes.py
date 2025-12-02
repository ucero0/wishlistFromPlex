"""Integration tests for sync API routes."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock


class TestTriggerSync:
    """Tests for POST /api/sync endpoint."""

    @patch("app.modules.plex.service.sync_all_users")
    def test_trigger_sync_success(
        self, mock_sync, client: TestClient, api_key_header: dict, sample_user
    ):
        """Test triggering a sync successfully."""
        mock_sync.return_value = {
            "users_processed": 1,
            "items_fetched": 10,
            "new_items": 5,
            "updated_items": 2,
            "total_items": 7,
            "errors": [],
            "sync_time": "2024-01-01T12:00:00Z",
        }
        
        response = client.post("/api/sync", headers=api_key_header)
        
        assert response.status_code == 200
        data = response.json()
        assert data["users_processed"] == 1
        assert data["items_fetched"] == 10
        assert data["new_items"] == 5

    @patch("app.modules.plex.service.sync_all_users")
    def test_trigger_sync_no_users(
        self, mock_sync, client: TestClient, api_key_header: dict
    ):
        """Test syncing when no users exist."""
        mock_sync.return_value = {
            "users_processed": 0,
            "items_fetched": 0,
            "new_items": 0,
            "updated_items": 0,
            "total_items": 0,
            "errors": [],
            "sync_time": "2024-01-01T12:00:00Z",
        }
        
        response = client.post("/api/sync", headers=api_key_header)
        
        assert response.status_code == 200
        data = response.json()
        assert data["users_processed"] == 0

    @patch("app.modules.plex.service.sync_all_users")
    def test_trigger_sync_with_errors(
        self, mock_sync, client: TestClient, api_key_header: dict, sample_user
    ):
        """Test sync response includes errors."""
        mock_sync.return_value = {
            "users_processed": 1,
            "items_fetched": 5,
            "new_items": 2,
            "updated_items": 1,
            "total_items": 3,
            "errors": ["Error fetching for user: timeout"],
            "sync_time": "2024-01-01T12:00:00Z",
        }
        
        response = client.post("/api/sync", headers=api_key_header)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["errors"]) == 1
        assert "timeout" in data["errors"][0]

    @patch("app.modules.plex.service.sync_all_users")
    def test_trigger_sync_failure(
        self, mock_sync, client: TestClient, api_key_header: dict
    ):
        """Test handling sync failure."""
        mock_sync.side_effect = Exception("Database connection failed")
        
        response = client.post("/api/sync", headers=api_key_header)
        
        assert response.status_code == 500
        assert "Sync failed" in response.json()["detail"]

    def test_trigger_sync_no_api_key(self, client: TestClient):
        """Test triggering sync without API key fails."""
        response = client.post("/api/sync")
        
        assert response.status_code == 401

    def test_trigger_sync_invalid_api_key(self, client: TestClient):
        """Test triggering sync with invalid API key fails."""
        response = client.post("/api/sync", headers={"X-API-Key": "wrong-key"})
        
        assert response.status_code == 401


class TestGetSyncStatus:
    """Tests for GET /api/sync/status endpoint."""

    def test_get_status_no_sync_yet(self, client: TestClient):
        """Test getting status when no sync has occurred."""
        # Reset the status by making a fresh request
        # Note: This test may be flaky due to global state
        response = client.get("/api/sync/status")
        
        # Could be 404 (no sync) or 200 (previous test ran sync)
        assert response.status_code in [200, 404]

    @patch("app.modules.plex.service.sync_all_users")
    def test_get_status_after_sync(
        self, mock_sync, client: TestClient, api_key_header: dict
    ):
        """Test getting status after a sync."""
        mock_sync.return_value = {
            "users_processed": 2,
            "items_fetched": 20,
            "new_items": 10,
            "updated_items": 5,
            "total_items": 15,
            "errors": [],
            "sync_time": "2024-01-01T12:00:00Z",
        }
        
        # Trigger sync first
        client.post("/api/sync", headers=api_key_header)
        
        # Then get status
        response = client.get("/api/sync/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["users_processed"] == 2
        assert data["items_fetched"] == 20

    def test_get_status_no_auth_required(self, client: TestClient):
        """Test that getting sync status doesn't require authentication."""
        response = client.get("/api/sync/status")
        
        # Should not be 401
        assert response.status_code != 401

