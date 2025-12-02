"""Integration tests for wishlist API routes."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock


class TestGetWishlist:
    """Tests for GET /api/wishlist endpoint."""

    def test_get_wishlist_empty(self, client: TestClient):
        """Test getting wishlist when empty."""
        response = client.get("/api/wishlist")
        
        assert response.status_code == 200
        assert response.json() == []

    def test_get_wishlist_with_items(self, client: TestClient, multiple_wishlist_items):
        """Test getting wishlist with items."""
        response = client.get("/api/wishlist")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 4

    def test_get_wishlist_search(self, client: TestClient, multiple_wishlist_items):
        """Test searching wishlist by title."""
        response = client.get("/api/wishlist?search=Matrix")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all("Matrix" in item["title"] for item in data)

    def test_get_wishlist_search_case_insensitive(self, client: TestClient, multiple_wishlist_items):
        """Test that search is case insensitive."""
        response = client.get("/api/wishlist?search=matrix")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_get_wishlist_filter_by_year(self, client: TestClient, multiple_wishlist_items):
        """Test filtering wishlist by year."""
        response = client.get("/api/wishlist?year=1999")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["year"] == 1999

    def test_get_wishlist_filter_by_media_type(self, client: TestClient, multiple_wishlist_items):
        """Test filtering wishlist by media type."""
        response = client.get("/api/wishlist?media_type=show")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "Breaking Bad"

    def test_get_wishlist_pagination_limit(self, client: TestClient, multiple_wishlist_items):
        """Test wishlist pagination with limit."""
        response = client.get("/api/wishlist?limit=2")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_get_wishlist_pagination_offset(self, client: TestClient, multiple_wishlist_items):
        """Test wishlist pagination with offset."""
        response = client.get("/api/wishlist?offset=2&limit=10")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_get_wishlist_combined_filters(self, client: TestClient, multiple_wishlist_items):
        """Test combining search and filters."""
        response = client.get("/api/wishlist?search=Matrix&year=1999")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "The Matrix"


class TestGetWishlistStats:
    """Tests for GET /api/wishlist/stats/summary endpoint."""

    def test_get_stats_empty(self, client: TestClient):
        """Test getting stats when wishlist is empty."""
        response = client.get("/api/wishlist/stats/summary")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_items"] == 0
        assert data["items_by_year"] == {}

    def test_get_stats_with_items(self, client: TestClient, multiple_wishlist_items):
        """Test getting stats with items."""
        response = client.get("/api/wishlist/stats/summary")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_items"] == 4
        assert "1999" in data["items_by_year"]
        assert data["items_by_type"]["movie"] == 3
        assert data["items_by_type"]["show"] == 1


class TestGetWishlistItem:
    """Tests for GET /api/wishlist/{guid} endpoint."""

    def test_get_item_success(self, client: TestClient, sample_wishlist_item):
        """Test getting a specific wishlist item."""
        response = client.get(f"/api/wishlist/{sample_wishlist_item.guid}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["guid"] == sample_wishlist_item.guid
        assert data["title"] == "Inception"

    def test_get_item_not_found(self, client: TestClient):
        """Test getting a non-existent item."""
        response = client.get("/api/wishlist/plex://movie/nonexistent")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


class TestRemoveWishlistItem:
    """Tests for DELETE /api/wishlist/remove/{guid} endpoint."""

    @patch("app.modules.plex.service.remove_from_watchlist")
    def test_remove_item_success(
        self, mock_remove, client: TestClient, sample_wishlist_item_with_source
    ):
        """Test removing a wishlist item successfully."""
        mock_remove.return_value = True
        
        response = client.delete(
            f"/api/wishlist/remove/{sample_wishlist_item_with_source.guid}"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "Successfully removed" in data["message"]

    def test_remove_item_not_found(self, client: TestClient):
        """Test removing a non-existent item."""
        response = client.delete("/api/wishlist/remove/plex://movie/nonexistent")
        
        assert response.status_code == 404

    def test_remove_item_no_sources(self, client: TestClient, sample_wishlist_item):
        """Test removing an item with no user sources."""
        response = client.delete(
            f"/api/wishlist/remove/{sample_wishlist_item.guid}"
        )
        
        assert response.status_code == 400
        assert "No users associated" in response.json()["detail"]

    @patch("app.modules.plex.service.remove_from_watchlist")
    def test_remove_item_plex_api_failure(
        self, mock_remove, client: TestClient, sample_wishlist_item_with_source
    ):
        """Test handling Plex API failure during removal."""
        mock_remove.return_value = False
        
        response = client.delete(
            f"/api/wishlist/remove/{sample_wishlist_item_with_source.guid}"
        )
        
        assert response.status_code == 500


class TestRemoveWishlistItemByRatingKey:
    """Tests for DELETE /api/wishlist/remove-by-rating-key/{rating_key} endpoint."""

    @patch("app.modules.plex.service.remove_from_watchlist")
    def test_remove_by_rating_key_success(
        self, mock_remove, client: TestClient, sample_wishlist_item_with_source
    ):
        """Test removing by rating key successfully."""
        mock_remove.return_value = True
        
        response = client.delete(
            f"/api/wishlist/remove-by-rating-key/{sample_wishlist_item_with_source.rating_key}"
        )
        
        assert response.status_code == 200
        assert "Successfully removed" in response.json()["message"]

    def test_remove_by_rating_key_not_found(self, client: TestClient):
        """Test removing by non-existent rating key."""
        response = client.delete("/api/wishlist/remove-by-rating-key/99999")
        
        assert response.status_code == 404

