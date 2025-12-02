"""Tests for Pydantic schemas."""
import pytest
from datetime import datetime, timezone
from pydantic import ValidationError

from app.modules.plex.schemas import (
    PlexUserCreate,
    PlexUserUpdate,
    PlexUserResponse,
    WishlistItemResponse,
    WishlistStatsResponse,
    PlexItemData,
    PlexAccountInfo,
    SyncResponse,
    MediaTypeEnum,
)


class TestPlexUserSchemas:
    """Tests for Plex user schemas."""

    def test_plex_user_create_valid(self):
        """Test creating a valid PlexUserCreate schema."""
        user = PlexUserCreate(name="TestUser", token="abc123token")
        assert user.name == "TestUser"
        assert user.token == "abc123token"

    def test_plex_user_create_missing_name(self):
        """Test PlexUserCreate fails without name."""
        with pytest.raises(ValidationError):
            PlexUserCreate(token="abc123token")

    def test_plex_user_create_missing_token(self):
        """Test PlexUserCreate fails without token."""
        with pytest.raises(ValidationError):
            PlexUserCreate(name="TestUser")

    def test_plex_user_update_all_fields(self):
        """Test PlexUserUpdate with all fields."""
        update = PlexUserUpdate(name="NewName", active=False)
        assert update.name == "NewName"
        assert update.active is False

    def test_plex_user_update_partial(self):
        """Test PlexUserUpdate with partial fields."""
        update = PlexUserUpdate(name="NewName")
        assert update.name == "NewName"
        assert update.active is None

    def test_plex_user_update_empty(self):
        """Test PlexUserUpdate with no fields."""
        update = PlexUserUpdate()
        assert update.name is None
        assert update.active is None

    def test_plex_user_response_valid(self):
        """Test PlexUserResponse with valid data."""
        now = datetime.now(timezone.utc)
        response = PlexUserResponse(
            id=1,
            name="TestUser",
            token_masked="abc1****en12",
            active=True,
            created_at=now,
            updated_at=now,
        )
        assert response.id == 1
        assert response.name == "TestUser"
        assert response.token_masked == "abc1****en12"
        assert response.active is True


class TestWishlistItemSchemas:
    """Tests for wishlist item schemas."""

    def test_wishlist_item_response_full(self):
        """Test WishlistItemResponse with all fields."""
        now = datetime.now(timezone.utc)
        response = WishlistItemResponse(
            id=1,
            guid="plex://movie/abc123",
            rating_key="12345",
            title="Test Movie",
            year=2024,
            media_type="movie",
            summary="A test movie summary",
            thumb="/thumb/path",
            art="/art/path",
            content_rating="PG-13",
            studio="Test Studio",
            added_at=now,
            last_seen_at=now,
        )
        assert response.id == 1
        assert response.guid == "plex://movie/abc123"
        assert response.title == "Test Movie"
        assert response.year == 2024
        assert response.media_type == "movie"

    def test_wishlist_item_response_minimal(self):
        """Test WishlistItemResponse with minimal fields."""
        now = datetime.now(timezone.utc)
        response = WishlistItemResponse(
            id=1,
            guid="plex://movie/abc123",
            title="Test Movie",
            added_at=now,
            last_seen_at=now,
        )
        assert response.id == 1
        assert response.rating_key is None
        assert response.year is None
        assert response.media_type is None

    def test_wishlist_stats_response(self):
        """Test WishlistStatsResponse schema."""
        stats = WishlistStatsResponse(
            total_items=100,
            items_by_year={"2024": 10, "2023": 20},
            items_by_type={"movie": 70, "show": 30},
        )
        assert stats.total_items == 100
        assert stats.items_by_year["2024"] == 10
        assert stats.items_by_type["movie"] == 70


class TestPlexAPISchemas:
    """Tests for Plex API data schemas."""

    def test_plex_item_data_full(self):
        """Test PlexItemData with all fields."""
        item = PlexItemData(
            guid="plex://movie/test123",
            rating_key="99999",
            title="Test Movie",
            year=2024,
            media_type="movie",
            summary="Test summary",
            thumb="/thumb",
            art="/art",
            content_rating="PG",
            studio="Test Studio",
        )
        assert item.guid == "plex://movie/test123"
        assert item.rating_key == "99999"
        assert item.media_type == "movie"

    def test_plex_item_data_minimal(self):
        """Test PlexItemData with minimal required fields."""
        item = PlexItemData(
            guid="plex://movie/test123",
            title="Test Movie",
        )
        assert item.guid == "plex://movie/test123"
        assert item.title == "Test Movie"
        assert item.rating_key is None
        assert item.year is None

    def test_plex_account_info(self):
        """Test PlexAccountInfo schema."""
        account = PlexAccountInfo(
            username="testuser",
            email="test@example.com",
            title="Test User",
            uuid="uuid-12345",
        )
        assert account.username == "testuser"
        assert account.email == "test@example.com"
        assert account.uuid == "uuid-12345"


class TestSyncSchemas:
    """Tests for sync-related schemas."""

    def test_sync_response_success(self):
        """Test SyncResponse for successful sync."""
        response = SyncResponse(
            users_processed=3,
            items_fetched=150,
            new_items=25,
            updated_items=10,
            total_items=100,
            errors=[],
            sync_time="2024-01-01T12:00:00Z",
        )
        assert response.users_processed == 3
        assert response.items_fetched == 150
        assert response.new_items == 25
        assert response.errors == []

    def test_sync_response_with_errors(self):
        """Test SyncResponse with errors."""
        response = SyncResponse(
            users_processed=2,
            items_fetched=50,
            new_items=5,
            updated_items=2,
            total_items=30,
            errors=["Error fetching user 1", "Timeout for user 2"],
            sync_time="2024-01-01T12:00:00Z",
        )
        assert len(response.errors) == 2
        assert "Error fetching user 1" in response.errors


class TestMediaTypeEnum:
    """Tests for MediaTypeEnum."""

    def test_media_type_values(self):
        """Test MediaTypeEnum values."""
        assert MediaTypeEnum.MOVIE.value == "movie"
        assert MediaTypeEnum.SHOW.value == "show"
        assert MediaTypeEnum.SEASON.value == "season"
        assert MediaTypeEnum.EPISODE.value == "episode"

    def test_media_type_from_string(self):
        """Test creating MediaTypeEnum from string."""
        assert MediaTypeEnum("movie") == MediaTypeEnum.MOVIE
        assert MediaTypeEnum("show") == MediaTypeEnum.SHOW

