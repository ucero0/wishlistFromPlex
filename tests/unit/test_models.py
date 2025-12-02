"""Tests for SQLAlchemy models."""
import pytest
from datetime import datetime, timezone
from sqlalchemy.exc import IntegrityError

from app.modules.plex.models import PlexUser, WishlistItem, WishlistItemSource, MediaType


class TestPlexUserModel:
    """Tests for PlexUser model."""

    def test_create_user(self, db_session):
        """Test creating a Plex user."""
        user = PlexUser(
            name="TestUser",
            plex_token="test-token-123",
            active=True,
        )
        db_session.add(user)
        db_session.commit()
        
        assert user.id is not None
        assert user.name == "TestUser"
        assert user.plex_token == "test-token-123"
        assert user.active is True
        assert user.created_at is not None
        assert user.updated_at is not None

    def test_user_default_active(self, db_session):
        """Test that user is active by default."""
        user = PlexUser(name="TestUser", plex_token="token")
        db_session.add(user)
        db_session.commit()
        
        assert user.active is True

    def test_user_unique_constraint(self, db_session):
        """Test that user names can be duplicated (no unique constraint)."""
        user1 = PlexUser(name="SameName", plex_token="token1")
        user2 = PlexUser(name="SameName", plex_token="token2")
        
        db_session.add(user1)
        db_session.add(user2)
        # Should not raise - names are not unique at DB level
        db_session.commit()
        
        assert user1.id != user2.id

    def test_user_relationship_to_sources(self, db_session, sample_user, sample_wishlist_item):
        """Test user relationship to wishlist sources."""
        source = WishlistItemSource(
            wishlist_item_id=sample_wishlist_item.id,
            plex_user_id=sample_user.id,
        )
        db_session.add(source)
        db_session.commit()
        
        db_session.refresh(sample_user)
        assert len(sample_user.wishlist_sources) == 1
        assert sample_user.wishlist_sources[0].wishlist_item_id == sample_wishlist_item.id


class TestWishlistItemModel:
    """Tests for WishlistItem model."""

    def test_create_wishlist_item_minimal(self, db_session):
        """Test creating a wishlist item with minimal fields."""
        item = WishlistItem(
            guid="plex://movie/test123",
            title="Test Movie",
        )
        db_session.add(item)
        db_session.commit()
        
        assert item.id is not None
        assert item.guid == "plex://movie/test123"
        assert item.title == "Test Movie"
        assert item.added_at is not None

    def test_create_wishlist_item_full(self, db_session):
        """Test creating a wishlist item with all fields."""
        item = WishlistItem(
            guid="plex://movie/full123",
            rating_key="12345",
            title="Full Test Movie",
            year=2024,
            media_type=MediaType.MOVIE,
            summary="A full test movie",
            thumb="/thumb/path",
            art="/art/path",
            content_rating="PG-13",
            studio="Test Studios",
        )
        db_session.add(item)
        db_session.commit()
        
        assert item.rating_key == "12345"
        assert item.year == 2024
        assert item.media_type == MediaType.MOVIE
        assert item.studio == "Test Studios"

    def test_wishlist_item_guid_unique(self, db_session):
        """Test that GUID must be unique."""
        item1 = WishlistItem(guid="plex://same/guid", title="Movie 1")
        item2 = WishlistItem(guid="plex://same/guid", title="Movie 2")
        
        db_session.add(item1)
        db_session.commit()
        
        db_session.add(item2)
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_wishlist_item_media_types(self, db_session):
        """Test different media types."""
        items = [
            WishlistItem(guid="plex://movie/1", title="Movie", media_type=MediaType.MOVIE),
            WishlistItem(guid="plex://show/1", title="Show", media_type=MediaType.SHOW),
            WishlistItem(guid="plex://season/1", title="Season", media_type=MediaType.SEASON),
            WishlistItem(guid="plex://episode/1", title="Episode", media_type=MediaType.EPISODE),
        ]
        
        for item in items:
            db_session.add(item)
        db_session.commit()
        
        movie = db_session.query(WishlistItem).filter(WishlistItem.media_type == MediaType.MOVIE).first()
        assert movie.title == "Movie"
        
        show = db_session.query(WishlistItem).filter(WishlistItem.media_type == MediaType.SHOW).first()
        assert show.title == "Show"


class TestWishlistItemSourceModel:
    """Tests for WishlistItemSource model."""

    def test_create_source(self, db_session, sample_user, sample_wishlist_item):
        """Test creating a wishlist item source."""
        source = WishlistItemSource(
            wishlist_item_id=sample_wishlist_item.id,
            plex_user_id=sample_user.id,
        )
        db_session.add(source)
        db_session.commit()
        
        assert source.id is not None
        assert source.wishlist_item_id == sample_wishlist_item.id
        assert source.plex_user_id == sample_user.id
        assert source.first_added_at is not None
        assert source.last_seen_at is not None

    def test_source_relationship_to_item(self, db_session, sample_user, sample_wishlist_item):
        """Test source relationship to wishlist item."""
        source = WishlistItemSource(
            wishlist_item_id=sample_wishlist_item.id,
            plex_user_id=sample_user.id,
        )
        db_session.add(source)
        db_session.commit()
        db_session.refresh(source)
        
        assert source.wishlist_item.title == sample_wishlist_item.title
        assert source.plex_user.name == sample_user.name

    def test_source_cascade_delete_from_item(self, db_session, sample_user, sample_wishlist_item):
        """Test that deleting item cascades to sources."""
        source = WishlistItemSource(
            wishlist_item_id=sample_wishlist_item.id,
            plex_user_id=sample_user.id,
        )
        db_session.add(source)
        db_session.commit()
        
        source_id = source.id
        
        # Delete the wishlist item
        db_session.delete(sample_wishlist_item)
        db_session.commit()
        
        # Source should be deleted
        deleted_source = db_session.query(WishlistItemSource).filter(
            WishlistItemSource.id == source_id
        ).first()
        assert deleted_source is None

    def test_source_cascade_delete_from_user(self, db_session, sample_user, sample_wishlist_item):
        """Test that deleting user cascades to sources."""
        source = WishlistItemSource(
            wishlist_item_id=sample_wishlist_item.id,
            plex_user_id=sample_user.id,
        )
        db_session.add(source)
        db_session.commit()
        
        source_id = source.id
        
        # Delete the user
        db_session.delete(sample_user)
        db_session.commit()
        
        # Source should be deleted
        deleted_source = db_session.query(WishlistItemSource).filter(
            WishlistItemSource.id == source_id
        ).first()
        assert deleted_source is None

    def test_multiple_users_same_item(self, db_session, sample_wishlist_item):
        """Test multiple users can have the same wishlist item."""
        user1 = PlexUser(name="User1", plex_token="token1")
        user2 = PlexUser(name="User2", plex_token="token2")
        db_session.add_all([user1, user2])
        db_session.commit()
        
        source1 = WishlistItemSource(
            wishlist_item_id=sample_wishlist_item.id,
            plex_user_id=user1.id,
        )
        source2 = WishlistItemSource(
            wishlist_item_id=sample_wishlist_item.id,
            plex_user_id=user2.id,
        )
        db_session.add_all([source1, source2])
        db_session.commit()
        
        db_session.refresh(sample_wishlist_item)
        assert len(sample_wishlist_item.sources) == 2


class TestMediaTypeEnum:
    """Tests for MediaType enum."""

    def test_media_type_values(self):
        """Test MediaType enum values."""
        assert MediaType.MOVIE.value == "movie"
        assert MediaType.SHOW.value == "show"
        assert MediaType.SEASON.value == "season"
        assert MediaType.EPISODE.value == "episode"

    def test_media_type_comparison(self, db_session):
        """Test comparing media types in queries."""
        item = WishlistItem(
            guid="plex://movie/compare",
            title="Compare Movie",
            media_type=MediaType.MOVIE,
        )
        db_session.add(item)
        db_session.commit()
        
        result = db_session.query(WishlistItem).filter(
            WishlistItem.media_type == MediaType.MOVIE
        ).first()
        
        assert result is not None
        assert result.media_type == MediaType.MOVIE
