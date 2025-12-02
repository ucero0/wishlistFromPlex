"""Integration tests for user API routes."""
import pytest
from fastapi.testclient import TestClient


class TestCreateUser:
    """Tests for POST /api/users endpoint."""

    def test_create_user_success(self, client: TestClient, api_key_header: dict):
        """Test creating a user successfully."""
        response = client.post(
            "/api/users",
            json={"name": "NewUser", "token": "new-token-abc123"},
            headers=api_key_header,
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "NewUser"
        assert data["active"] is True
        assert "****" in data["token_masked"]
        assert data["id"] is not None

    def test_create_user_duplicate_name(self, client: TestClient, api_key_header: dict, sample_user):
        """Test creating a user with duplicate name fails."""
        response = client.post(
            "/api/users",
            json={"name": "TestUser", "token": "another-token"},
            headers=api_key_header,
        )
        
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    def test_create_user_no_api_key(self, client: TestClient):
        """Test creating a user without API key fails."""
        response = client.post(
            "/api/users",
            json={"name": "NewUser", "token": "token"},
        )
        
        assert response.status_code == 401

    def test_create_user_invalid_api_key(self, client: TestClient):
        """Test creating a user with invalid API key fails."""
        response = client.post(
            "/api/users",
            json={"name": "NewUser", "token": "token"},
            headers={"X-API-Key": "wrong-key"},
        )
        
        assert response.status_code == 401

    def test_create_user_missing_name(self, client: TestClient, api_key_header: dict):
        """Test creating a user without name fails."""
        response = client.post(
            "/api/users",
            json={"token": "token"},
            headers=api_key_header,
        )
        
        assert response.status_code == 422

    def test_create_user_missing_token(self, client: TestClient, api_key_header: dict):
        """Test creating a user without token fails."""
        response = client.post(
            "/api/users",
            json={"name": "NewUser"},
            headers=api_key_header,
        )
        
        assert response.status_code == 422


class TestListUsers:
    """Tests for GET /api/users endpoint."""

    def test_list_users_empty(self, client: TestClient):
        """Test listing users when none exist."""
        response = client.get("/api/users")
        
        assert response.status_code == 200
        assert response.json() == []

    def test_list_users_single(self, client: TestClient, sample_user):
        """Test listing a single user."""
        response = client.get("/api/users")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "TestUser"
        assert "****" in data[0]["token_masked"]

    def test_list_users_multiple(self, client: TestClient, sample_user, sample_inactive_user):
        """Test listing multiple users."""
        response = client.get("/api/users")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_list_users_no_auth_required(self, client: TestClient, sample_user):
        """Test that listing users doesn't require authentication."""
        response = client.get("/api/users")
        
        assert response.status_code == 200


class TestGetUser:
    """Tests for GET /api/users/{user_id} endpoint."""

    def test_get_user_success(self, client: TestClient, sample_user):
        """Test getting a specific user."""
        response = client.get(f"/api/users/{sample_user.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_user.id
        assert data["name"] == "TestUser"

    def test_get_user_not_found(self, client: TestClient):
        """Test getting a non-existent user."""
        response = client.get("/api/users/99999")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


class TestUpdateUser:
    """Tests for PATCH /api/users/{user_id} endpoint."""

    def test_update_user_name(self, client: TestClient, api_key_header: dict, sample_user):
        """Test updating a user's name."""
        response = client.patch(
            f"/api/users/{sample_user.id}",
            json={"name": "UpdatedName"},
            headers=api_key_header,
        )
        
        assert response.status_code == 200
        assert response.json()["name"] == "UpdatedName"

    def test_update_user_active_status(self, client: TestClient, api_key_header: dict, sample_user):
        """Test updating a user's active status."""
        response = client.patch(
            f"/api/users/{sample_user.id}",
            json={"active": False},
            headers=api_key_header,
        )
        
        assert response.status_code == 200
        assert response.json()["active"] is False

    def test_update_user_both_fields(self, client: TestClient, api_key_header: dict, sample_user):
        """Test updating both name and active status."""
        response = client.patch(
            f"/api/users/{sample_user.id}",
            json={"name": "NewName", "active": False},
            headers=api_key_header,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "NewName"
        assert data["active"] is False

    def test_update_user_not_found(self, client: TestClient, api_key_header: dict):
        """Test updating a non-existent user."""
        response = client.patch(
            "/api/users/99999",
            json={"name": "NewName"},
            headers=api_key_header,
        )
        
        assert response.status_code == 404

    def test_update_user_duplicate_name(
        self, client: TestClient, api_key_header: dict, sample_user, sample_inactive_user
    ):
        """Test updating to a name that already exists."""
        response = client.patch(
            f"/api/users/{sample_user.id}",
            json={"name": "InactiveUser"},
            headers=api_key_header,
        )
        
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    def test_update_user_no_api_key(self, client: TestClient, sample_user):
        """Test updating a user without API key fails."""
        response = client.patch(
            f"/api/users/{sample_user.id}",
            json={"name": "NewName"},
        )
        
        assert response.status_code == 401


class TestDeleteUser:
    """Tests for DELETE /api/users/{user_id} endpoint."""

    def test_delete_user_success(self, client: TestClient, api_key_header: dict, sample_user):
        """Test soft deleting a user."""
        response = client.delete(
            f"/api/users/{sample_user.id}",
            headers=api_key_header,
        )
        
        assert response.status_code == 204
        
        # Verify user is now inactive
        get_response = client.get(f"/api/users/{sample_user.id}")
        assert get_response.json()["active"] is False

    def test_delete_user_not_found(self, client: TestClient, api_key_header: dict):
        """Test deleting a non-existent user."""
        response = client.delete(
            "/api/users/99999",
            headers=api_key_header,
        )
        
        assert response.status_code == 404

    def test_delete_user_no_api_key(self, client: TestClient, sample_user):
        """Test deleting a user without API key fails."""
        response = client.delete(f"/api/users/{sample_user.id}")
        
        assert response.status_code == 401

