import pytest
from app.models.plex_user import PlexUser


class TestTokenRoutes:
    """Tests for token/user management routes."""
    
    def test_create_user_success(self, client, sample_plex_user_data):
        """Test creating a user successfully."""
        response = client.post(
            "/api/users",
            json=sample_plex_user_data,
            headers={"X-API-Key": "test-api-key"},
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test User"
        assert "token_masked" in data
        assert data["token_masked"] != sample_plex_user_data["token"]  # Should be masked
        assert data["active"] is True
    
    def test_create_user_missing_api_key(self, client, sample_plex_user_data):
        """Test creating user without API key."""
        response = client.post(
            "/api/users",
            json=sample_plex_user_data,
        )
        
        assert response.status_code == 401
    
    def test_create_user_duplicate_name(self, client, db_session, sample_plex_user_data):
        """Test creating user with duplicate name."""
        # Create first user
        client.post(
            "/api/users",
            json=sample_plex_user_data,
            headers={"X-API-Key": "test-api-key"},
        )
        
        # Try to create another with same name
        response = client.post(
            "/api/users",
            json=sample_plex_user_data,
            headers={"X-API-Key": "test-api-key"},
        )
        
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()
    
    def test_list_users(self, client, db_session):
        """Test listing all users."""
        # Create a user directly in DB
        user = PlexUser(name="Test User", plex_token="test-token", active=True)
        db_session.add(user)
        db_session.commit()
        
        response = client.get("/api/users")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["name"] == "Test User"
        assert "token_masked" in data[0]
    
    def test_list_users_empty(self, client):
        """Test listing users when none exist."""
        response = client.get("/api/users")
        
        assert response.status_code == 200
        assert response.json() == []
    
    def test_get_user_by_id(self, client, db_session):
        """Test getting a specific user by ID."""
        user = PlexUser(name="Test User", plex_token="test-token", active=True)
        db_session.add(user)
        db_session.commit()
        
        response = client.get(f"/api/users/{user.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == user.id
        assert data["name"] == "Test User"
    
    def test_get_user_not_found(self, client):
        """Test getting non-existent user."""
        response = client.get("/api/users/99999")
        
        assert response.status_code == 404
    
    def test_update_user(self, client, db_session):
        """Test updating a user."""
        user = PlexUser(name="Old Name", plex_token="test-token", active=True)
        db_session.add(user)
        db_session.commit()
        
        response = client.patch(
            f"/api/users/{user.id}",
            json={"name": "New Name", "active": False},
            headers={"X-API-Key": "test-api-key"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Name"
        assert data["active"] is False
    
    def test_update_user_missing_api_key(self, client, db_session):
        """Test updating user without API key."""
        user = PlexUser(name="Test User", plex_token="test-token", active=True)
        db_session.add(user)
        db_session.commit()
        
        response = client.patch(
            f"/api/users/{user.id}",
            json={"name": "New Name"},
        )
        
        assert response.status_code == 401
    
    def test_delete_user(self, client, db_session):
        """Test soft deleting a user."""
        user = PlexUser(name="Test User", plex_token="test-token", active=True)
        db_session.add(user)
        db_session.commit()
        
        response = client.delete(
            f"/api/users/{user.id}",
            headers={"X-API-Key": "test-api-key"},
        )
        
        assert response.status_code == 204
        
        # Verify user is inactive
        db_session.refresh(user)
        assert user.active is False
    
    def test_delete_user_missing_api_key(self, client, db_session):
        """Test deleting user without API key."""
        user = PlexUser(name="Test User", plex_token="test-token", active=True)
        db_session.add(user)
        db_session.commit()
        
        response = client.delete(f"/api/users/{user.id}")
        
        assert response.status_code == 401

