"""Tests for Plex API routes."""
import pytest
from unittest.mock import patch, AsyncMock

from app.modules.plex.constants import USERS_PREFIX, WISHLIST_PREFIX, SYNC_PREFIX


class TestUsersRoutes:
    """Tests for Plex users endpoints."""

    def test_create_user_success(self, client, api_key_header):
        """Test creating a user successfully."""
        response = client.post(
            USERS_PREFIX,
            json={"name": "NewUser", "token": "new-token-123"},
            headers=api_key_header,
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "NewUser"
        assert data["active"] is True

    def test_create_user_no_api_key(self, client):
        """Test creating user without API key."""
        response = client.post(
            USERS_PREFIX,
            json={"name": "NewUser", "token": "token"},
        )
        
        assert response.status_code == 401

    def test_list_users(self, client, sample_user):
        """Test listing users."""
        response = client.get(USERS_PREFIX)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

    def test_get_user(self, client, sample_user):
        """Test getting a specific user."""
        response = client.get(f"{USERS_PREFIX}/{sample_user.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == sample_user.name

    def test_get_user_not_found(self, client):
        """Test getting non-existent user."""
        response = client.get(f"{USERS_PREFIX}/99999")
        
        assert response.status_code == 404

    def test_update_user(self, client, sample_user, api_key_header):
        """Test updating a user."""
        response = client.patch(
            f"{USERS_PREFIX}/{sample_user.id}",
            json={"name": "UpdatedName"},
            headers=api_key_header,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "UpdatedName"

    def test_delete_user(self, client, sample_user, api_key_header):
        """Test deleting a user."""
        response = client.delete(
            f"{USERS_PREFIX}/{sample_user.id}",
            headers=api_key_header,
        )
        
        assert response.status_code == 204


class TestWishlistRoutes:
    """Tests for Plex wishlist endpoints."""

    def test_get_wishlist_empty(self, client):
        """Test getting empty wishlist."""
        response = client.get(WISHLIST_PREFIX)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0

    def test_get_wishlist_with_items(self, client, multiple_wishlist_items):
        """Test getting wishlist with items."""
        response = client.get(WISHLIST_PREFIX)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 4

    def test_get_wishlist_search(self, client, multiple_wishlist_items):
        """Test searching wishlist."""
        response = client.get(f"{WISHLIST_PREFIX}?search=Matrix")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2  # Matrix and Matrix Reloaded

    def test_get_wishlist_filter_by_year(self, client, multiple_wishlist_items):
        """Test filtering by year."""
        response = client.get(f"{WISHLIST_PREFIX}?year=2014")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "Interstellar"

    def test_get_wishlist_filter_by_media_type(self, client, multiple_wishlist_items):
        """Test filtering by media type."""
        response = client.get(f"{WISHLIST_PREFIX}?media_type=show")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "Breaking Bad"

    def test_get_wishlist_item(self, client, sample_wishlist_item):
        """Test getting a specific wishlist item."""
        response = client.get(f"{WISHLIST_PREFIX}/{sample_wishlist_item.guid}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == sample_wishlist_item.title

    def test_get_wishlist_stats(self, client, multiple_wishlist_items):
        """Test getting wishlist stats."""
        response = client.get(f"{WISHLIST_PREFIX}/stats/summary")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_items"] == 4
        assert data["items_by_type"]["movie"] == 3
        assert data["items_by_type"]["show"] == 1

    @patch("app.modules.plex.service.remove_from_watchlist")
    def test_remove_wishlist_item(
        self, mock_remove, client, sample_wishlist_item_with_source, api_key_header
    ):
        """Test removing a wishlist item."""
        mock_remove.return_value = True
        
        response = client.delete(
            f"{WISHLIST_PREFIX}/remove/{sample_wishlist_item_with_source.guid}",
            headers=api_key_header,
        )
        
        assert response.status_code == 200


class TestSyncRoutes:
    """Tests for sync endpoints."""

    def test_trigger_sync_no_api_key(self, client):
        """Test triggering sync without API key."""
        response = client.post(SYNC_PREFIX)
        
        assert response.status_code == 401

    def test_trigger_sync_with_api_key(self, client, api_key_header, sample_user):
        """Test triggering sync with API key returns valid response."""
        response = client.post(SYNC_PREFIX, headers=api_key_header)
        
        # With a user, sync should return 200
        assert response.status_code == 200
        data = response.json()
        assert "users_processed" in data
