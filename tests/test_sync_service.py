import pytest
from unittest.mock import AsyncMock, patch

from app.models.plex_user import PlexUser
from app.models.wishlist_item import WishlistItem, WishlistItemSource
from app.services.sync_service import sync_all_users


@pytest.mark.asyncio
class TestSyncAllUsers:
    """Tests for sync_all_users function."""
    
    async def test_sync_no_users(self, db_session):
        """Test syncing with no active users."""
        result = await sync_all_users(db_session)
        
        assert result["users_processed"] == 0
        assert result["items_fetched"] == 0
        assert result["new_items"] == 0
        assert result["updated_items"] == 0
    
    @patch("app.services.sync_service.get_watchlist")
    async def test_sync_single_user_new_items(self, mock_get_watchlist, db_session):
        """Test syncing with one user and new items."""
        # Create a user
        user = PlexUser(
            name="Test User",
            plex_token="test-token-123",
            active=True,
        )
        db_session.add(user)
        db_session.commit()
        
        # Mock watchlist response
        mock_get_watchlist.return_value = [
            {
                "uid": "plex://movie/guid/tmdb://12345",
                "title": "Test Movie 1",
                "year": 2023,
            },
            {
                "uid": "plex://movie/guid/tmdb://67890",
                "title": "Test Movie 2",
                "year": 2024,
            },
        ]
        
        result = await sync_all_users(db_session)
        
        assert result["users_processed"] == 1
        assert result["items_fetched"] == 2
        assert result["new_items"] == 2
        assert result["updated_items"] == 0
        
        # Verify items in database
        items = db_session.query(WishlistItem).all()
        assert len(items) == 2
        
        # Verify sources
        sources = db_session.query(WishlistItemSource).all()
        assert len(sources) == 2
    
    @patch("app.services.sync_service.get_watchlist")
    async def test_sync_multiple_users_duplicate_items(self, mock_get_watchlist, db_session):
        """Test syncing with multiple users having duplicate items."""
        # Create two users
        user1 = PlexUser(name="User 1", plex_token="token-1", active=True)
        user2 = PlexUser(name="User 2", plex_token="token-2", active=True)
        db_session.add(user1)
        db_session.add(user2)
        db_session.commit()
        
        # Mock watchlist - both users have same movie
        def mock_watchlist(token):
            if token == "token-1":
                return [{"uid": "plex://movie/guid/tmdb://12345", "title": "Shared Movie", "year": 2023}]
            else:
                return [{"uid": "plex://movie/guid/tmdb://12345", "title": "Shared Movie", "year": 2023}]
        
        mock_get_watchlist.side_effect = mock_watchlist
        
        result = await sync_all_users(db_session)
        
        assert result["users_processed"] == 2
        assert result["items_fetched"] == 2  # Both users fetched
        assert result["new_items"] == 1  # Only one unique item
        assert result["updated_items"] == 0
        
        # Verify only one item in database
        items = db_session.query(WishlistItem).all()
        assert len(items) == 1
        
        # Verify both users are linked to the item
        sources = db_session.query(WishlistItemSource).all()
        assert len(sources) == 2
    
    @patch("app.services.sync_service.get_watchlist")
    async def test_sync_update_existing_item(self, mock_get_watchlist, db_session):
        """Test syncing updates existing items."""
        # Create existing item
        existing_item = WishlistItem(
            uid="plex://movie/guid/tmdb://12345",
            title="Old Title",
            year=2022,
        )
        db_session.add(existing_item)
        db_session.commit()
        
        # Create user
        user = PlexUser(name="Test User", plex_token="test-token", active=True)
        db_session.add(user)
        db_session.commit()
        
        # Mock watchlist with updated title and year
        mock_get_watchlist.return_value = [
            {
                "uid": "plex://movie/guid/tmdb://12345",
                "title": "New Title",
                "year": 2023,
            },
        ]
        
        result = await sync_all_users(db_session)
        
        assert result["new_items"] == 0
        assert result["updated_items"] == 1
        
        # Verify item was updated
        db_session.refresh(existing_item)
        assert existing_item.title == "New Title"
        assert existing_item.year == 2023
    
    @patch("app.services.sync_service.get_watchlist")
    async def test_sync_handles_errors_gracefully(self, mock_get_watchlist, db_session):
        """Test that sync handles errors for individual users gracefully."""
        from fastapi import HTTPException
        
        # Create two users
        user1 = PlexUser(name="User 1", plex_token="token-1", active=True)
        user2 = PlexUser(name="User 2", plex_token="token-2", active=True)
        db_session.add(user1)
        db_session.add(user2)
        db_session.commit()
        
        # Mock: first user succeeds, second fails
        def mock_watchlist(token):
            if token == "token-1":
                return [{"uid": "plex://movie/guid/tmdb://12345", "title": "Movie 1", "year": 2023}]
            else:
                raise HTTPException(status_code=401, detail="Invalid token")
        
        mock_get_watchlist.side_effect = mock_watchlist
        
        result = await sync_all_users(db_session)
        
        # Should process both users, but only one succeeds
        assert result["users_processed"] == 2
        assert len(result["errors"]) == 1
        
        # Should still have items from successful user
        items = db_session.query(WishlistItem).all()
        assert len(items) == 1
    
    @patch("app.services.sync_service.get_watchlist")
    async def test_sync_inactive_user_skipped(self, mock_get_watchlist, db_session):
        """Test that inactive users are skipped."""
        # Create active and inactive users
        active_user = PlexUser(name="Active User", plex_token="token-1", active=True)
        inactive_user = PlexUser(name="Inactive User", plex_token="token-2", active=False)
        db_session.add(active_user)
        db_session.add(inactive_user)
        db_session.commit()
        
        mock_get_watchlist.return_value = [
            {"uid": "plex://movie/guid/tmdb://12345", "title": "Movie 1", "year": 2023}
        ]
        
        result = await sync_all_users(db_session)
        
        # Should only process active user
        assert result["users_processed"] == 1
        # Verify get_watchlist was only called once
        assert mock_get_watchlist.call_count == 1

