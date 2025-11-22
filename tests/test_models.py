import pytest
from datetime import datetime, timezone

from app.models.plex_user import PlexUser
from app.models.wishlist_item import WishlistItem, WishlistItemSource


class TestPlexUser:
    """Tests for PlexUser model."""
    
    def test_create_plex_user(self, db_session):
        """Test creating a Plex user."""
        user = PlexUser(
            name="Test User",
            plex_token="test-token-123",
            active=True,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        assert user.id is not None
        assert user.name == "Test User"
        assert user.plex_token == "test-token-123"
        assert user.active is True
        assert user.created_at is not None
        assert user.updated_at is not None
    
    def test_plex_user_defaults(self, db_session):
        """Test Plex user default values."""
        user = PlexUser(
            name="Test User",
            plex_token="test-token-123",
        )
        db_session.add(user)
        db_session.commit()
        
        assert user.active is True  # Default value
    
    def test_plex_user_relationships(self, db_session):
        """Test Plex user relationships."""
        user = PlexUser(
            name="Test User",
            plex_token="test-token-123",
        )
        db_session.add(user)
        db_session.commit()
        
        # Check relationship exists
        assert hasattr(user, 'wishlist_sources')
        assert user.wishlist_sources == []


class TestWishlistItem:
    """Tests for WishlistItem model."""
    
    def test_create_wishlist_item(self, db_session):
        """Test creating a wishlist item."""
        item = WishlistItem(
            uid="plex://movie/guid/tmdb://12345",
            title="Test Movie",
            year=2023,
        )
        db_session.add(item)
        db_session.commit()
        db_session.refresh(item)
        
        assert item.id is not None
        assert item.uid == "plex://movie/guid/tmdb://12345"
        assert item.title == "Test Movie"
        assert item.year == 2023
        assert item.added_at is not None
        assert item.last_seen_at is not None
    
    def test_wishlist_item_without_year(self, db_session):
        """Test creating wishlist item without year."""
        item = WishlistItem(
            uid="plex://movie/guid/tmdb://12345",
            title="Test Movie",
            year=None,
        )
        db_session.add(item)
        db_session.commit()
        
        assert item.year is None
    
    def test_wishlist_item_unique_uid(self, db_session):
        """Test that uid must be unique."""
        item1 = WishlistItem(
            uid="plex://movie/guid/tmdb://12345",
            title="Test Movie 1",
        )
        db_session.add(item1)
        db_session.commit()
        
        item2 = WishlistItem(
            uid="plex://movie/guid/tmdb://12345",
            title="Test Movie 2",
        )
        db_session.add(item2)
        
        with pytest.raises(Exception):  # IntegrityError
            db_session.commit()
    
    def test_wishlist_item_relationships(self, db_session):
        """Test wishlist item relationships."""
        item = WishlistItem(
            uid="plex://movie/guid/tmdb://12345",
            title="Test Movie",
        )
        db_session.add(item)
        db_session.commit()
        
        assert hasattr(item, 'sources')
        assert item.sources == []


class TestWishlistItemSource:
    """Tests for WishlistItemSource model."""
    
    def test_create_wishlist_item_source(self, db_session):
        """Test creating a wishlist item source."""
        # Create user and item first
        user = PlexUser(
            name="Test User",
            plex_token="test-token-123",
        )
        item = WishlistItem(
            uid="plex://movie/guid/tmdb://12345",
            title="Test Movie",
        )
        db_session.add(user)
        db_session.add(item)
        db_session.commit()
        
        # Create source
        source = WishlistItemSource(
            wishlist_item_id=item.id,
            plex_user_id=user.id,
        )
        db_session.add(source)
        db_session.commit()
        db_session.refresh(source)
        
        assert source.id is not None
        assert source.wishlist_item_id == item.id
        assert source.plex_user_id == user.id
        assert source.first_added_at is not None
        assert source.last_seen_at is not None
    
    def test_wishlist_item_source_relationships(self, db_session):
        """Test wishlist item source relationships."""
        user = PlexUser(
            name="Test User",
            plex_token="test-token-123",
        )
        item = WishlistItem(
            uid="plex://movie/guid/tmdb://12345",
            title="Test Movie",
        )
        db_session.add(user)
        db_session.add(item)
        db_session.commit()
        
        source = WishlistItemSource(
            wishlist_item_id=item.id,
            plex_user_id=user.id,
        )
        db_session.add(source)
        db_session.commit()
        db_session.refresh(source)
        
        assert source.wishlist_item.id == item.id
        assert source.plex_user.id == user.id

