"""Tests for Plex service layer with mocked HTTP API calls."""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timezone

from app.modules.plex.service import (
    verify_token,
    get_account_info,
    get_watchlist,
    remove_from_watchlist,
    add_to_watchlist,
    normalize_api_item,
    search_plex,
    parse_media_type,
    sync_all_users,
)
from app.modules.plex.schemas import PlexItemData
from app.modules.plex.models import PlexUser, WishlistItem, MediaType


class TestVerifyToken:
    """Tests for verify_token function."""

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_verify_valid_token(self, mock_client_class):
        """Test verifying a valid token."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client_class.return_value = mock_client
        
        result = await verify_token("valid-token")
        assert result is True

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_verify_invalid_token(self, mock_client_class):
        """Test verifying an invalid token."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client_class.return_value = mock_client
        
        result = await verify_token("invalid-token")
        assert result is False


class TestGetAccountInfo:
    """Tests for get_account_info function."""

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_get_account_info_success(self, mock_client_class):
        """Test getting account info successfully."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "username": "testuser",
            "email": "test@example.com",
            "title": "Test User",
            "uuid": "uuid-123",
        }
        
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client_class.return_value = mock_client
        
        result = await get_account_info("valid-token")
        
        assert result is not None
        assert result.username == "testuser"
        assert result.email == "test@example.com"

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_get_account_info_invalid_token(self, mock_client_class):
        """Test getting account info with invalid token."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client_class.return_value = mock_client
        
        result = await get_account_info("invalid-token")
        assert result is None


class TestGetWatchlist:
    """Tests for get_watchlist function."""

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_get_watchlist_success(self, mock_client_class):
        """Test fetching watchlist successfully."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "MediaContainer": {
                "Metadata": [
                    {
                        "guid": "plex://movie/123",
                        "ratingKey": "123",
                        "title": "Test Movie",
                        "year": 2024,
                        "type": "movie",
                    }
                ]
            }
        }
        
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client_class.return_value = mock_client
        
        result = await get_watchlist("valid-token")
        
        assert len(result) == 1
        assert isinstance(result[0], PlexItemData)
        assert result[0].title == "Test Movie"

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_get_watchlist_empty(self, mock_client_class):
        """Test handling empty watchlist."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"MediaContainer": {"Metadata": []}}
        
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client_class.return_value = mock_client
        
        result = await get_watchlist("valid-token")
        assert result == []

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_get_watchlist_api_error(self, mock_client_class):
        """Test handling API errors."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client_class.return_value = mock_client
        
        result = await get_watchlist("valid-token")
        assert result == []


class TestRemoveFromWatchlist:
    """Tests for remove_from_watchlist function."""

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_remove_success(self, mock_client_class):
        """Test successful removal from watchlist."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        
        mock_client = AsyncMock()
        mock_client.put.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client_class.return_value = mock_client
        
        result = await remove_from_watchlist("token", "5d776d1847dd6e001f6f002f")
        assert result is True

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_remove_failure(self, mock_client_class):
        """Test failed removal from watchlist."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Not found"
        
        mock_client = AsyncMock()
        mock_client.put.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client_class.return_value = mock_client
        
        result = await remove_from_watchlist("token", "invalid_rating_key")
        assert result is False

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_remove_network_error(self, mock_client_class):
        """Test handling network errors."""
        mock_client = AsyncMock()
        mock_client.put.side_effect = Exception("Network error")
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client_class.return_value = mock_client
        
        result = await remove_from_watchlist("token", "5d776d1847dd6e001f6f002f")
        assert result is False


class TestAddToWatchlist:
    """Tests for add_to_watchlist function."""

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_add_success(self, mock_client_class):
        """Test successful addition to watchlist."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        
        mock_client = AsyncMock()
        mock_client.put.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client_class.return_value = mock_client
        
        result = await add_to_watchlist("token", "5d776d1847dd6e001f6f002f")
        assert result is True

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_add_failure(self, mock_client_class):
        """Test failed addition to watchlist."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad request"
        
        mock_client = AsyncMock()
        mock_client.put.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client_class.return_value = mock_client
        
        result = await add_to_watchlist("token", "5d776d1847dd6e001f6f002f")
        assert result is False


class TestSearchPlex:
    """Tests for search_plex function."""

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_search_success(self, mock_client_class):
        """Test searching Plex successfully."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "MediaContainer": {
                "SearchResults": [
                    {
                        "SearchResult": [
                            {
                                "Metadata": {
                                    "guid": "plex://movie/123",
                                    "title": "Test Movie",
                                    "year": 2024,
                                    "type": "movie",
                                }
                            }
                        ]
                    }
                ]
            }
        }
        
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client_class.return_value = mock_client
        
        result = await search_plex("token", "Test Movie")
        
        assert len(result) == 1
        assert result[0].title == "Test Movie"

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_search_no_results(self, mock_client_class):
        """Test search with no results."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"MediaContainer": {"SearchResults": []}}
        
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client_class.return_value = mock_client
        
        result = await search_plex("token", "nonexistent")
        assert result == []


class TestNormalizeApiItem:
    """Tests for normalize_api_item function."""

    def test_normalize_full_item(self):
        """Test normalizing a fully populated item."""
        item = {
            "guid": "plex://movie/123",
            "ratingKey": "123",
            "title": "Test Movie",
            "year": 2024,
            "type": "movie",
            "summary": "A test movie",
            "thumb": "/thumb/123",
            "art": "/art/123",
            "contentRating": "PG-13",
            "studio": "Test Studio",
        }
        
        result = normalize_api_item(item)
        
        assert result is not None
        assert result.guid == "plex://movie/123"
        assert result.title == "Test Movie"
        assert result.year == 2024
        assert result.media_type == "movie"
        assert result.studio == "Test Studio"

    def test_normalize_minimal_item(self):
        """Test normalizing an item with minimal fields."""
        item = {
            "guid": "plex://movie/minimal",
            "title": "Minimal Movie",
        }
        
        result = normalize_api_item(item)
        
        assert result is not None
        assert result.guid == "plex://movie/minimal"
        assert result.title == "Minimal Movie"
        assert result.year is None

    def test_normalize_missing_guid(self):
        """Test handling item without GUID but with ratingKey."""
        item = {
            "ratingKey": "12345",
            "title": "No GUID Movie",
            "type": "movie",
        }
        
        result = normalize_api_item(item)
        
        assert result is not None
        assert "plex://movie/12345" in result.guid

    def test_normalize_missing_title(self):
        """Test handling item without title."""
        item = {
            "guid": "plex://movie/notitle",
        }
        
        result = normalize_api_item(item)
        assert result is None

    def test_normalize_show_type(self):
        """Test normalizing a TV show."""
        item = {
            "guid": "plex://show/123",
            "title": "Test Show",
            "year": 2020,
            "type": "show",
        }
        
        result = normalize_api_item(item)
        
        assert result is not None
        assert result.media_type == "show"


class TestParseMediaType:
    """Tests for parse_media_type function."""

    def test_parse_movie(self):
        """Test parsing movie type."""
        result = parse_media_type("movie")
        assert result == MediaType.MOVIE

    def test_parse_show(self):
        """Test parsing show type."""
        result = parse_media_type("show")
        assert result == MediaType.SHOW

    def test_parse_season(self):
        """Test parsing season type."""
        result = parse_media_type("season")
        assert result == MediaType.SEASON

    def test_parse_episode(self):
        """Test parsing episode type."""
        result = parse_media_type("episode")
        assert result == MediaType.EPISODE

    def test_parse_uppercase(self):
        """Test parsing uppercase type."""
        result = parse_media_type("MOVIE")
        assert result == MediaType.MOVIE

    def test_parse_mixed_case(self):
        """Test parsing mixed case type."""
        result = parse_media_type("MoViE")
        assert result == MediaType.MOVIE

    def test_parse_unknown(self):
        """Test parsing unknown type."""
        result = parse_media_type("unknown")
        assert result is None

    def test_parse_none(self):
        """Test parsing None."""
        result = parse_media_type(None)
        assert result is None


class TestSyncAllUsers:
    """Tests for sync_all_users function."""

    @pytest.mark.asyncio
    @patch("app.modules.plex.service.get_watchlist")
    async def test_sync_success(self, mock_get_watchlist, db_session, sample_user):
        """Test successful sync."""
        mock_get_watchlist.return_value = [
            PlexItemData(
                guid="plex://movie/new123",
                title="New Movie",
                year=2024,
                media_type="movie",
            )
        ]
        
        result = await sync_all_users(db_session)
        
        assert result["users_processed"] == 1
        assert result["items_fetched"] == 1
        assert result["new_items"] == 1
        assert result["errors"] == []

    @pytest.mark.asyncio
    @patch("app.modules.plex.service.get_watchlist")
    async def test_sync_no_active_users(self, mock_get_watchlist, db_session):
        """Test sync with no active users."""
        result = await sync_all_users(db_session)
        
        assert result["users_processed"] == 0
        assert result["items_fetched"] == 0
        mock_get_watchlist.assert_not_called()

    @pytest.mark.asyncio
    @patch("app.modules.plex.service.get_watchlist")
    async def test_sync_updates_existing(
        self, mock_get_watchlist, db_session, sample_user, sample_wishlist_item
    ):
        """Test sync updates existing items."""
        mock_get_watchlist.return_value = [
            PlexItemData(
                guid=sample_wishlist_item.guid,
                title="Updated Inception",
                year=2010,
                media_type="movie",
            )
        ]
        
        result = await sync_all_users(db_session)
        
        assert result["users_processed"] == 1
        assert result["updated_items"] == 1
        assert result["new_items"] == 0
        
        # Verify update
        db_session.refresh(sample_wishlist_item)
        assert sample_wishlist_item.title == "Updated Inception"

    @pytest.mark.asyncio
    @patch("app.modules.plex.service.get_watchlist")
    async def test_sync_handles_errors(self, mock_get_watchlist, db_session, sample_user):
        """Test sync handles errors gracefully."""
        mock_get_watchlist.side_effect = Exception("API error")
        
        result = await sync_all_users(db_session)
        
        assert result["users_processed"] == 1
        assert len(result["errors"]) == 1
        assert "API error" in result["errors"][0]

    @pytest.mark.asyncio
    @patch("app.modules.plex.service.get_watchlist")
    async def test_sync_creates_sources(self, mock_get_watchlist, db_session, sample_user):
        """Test sync creates user-item relationships."""
        mock_get_watchlist.return_value = [
            PlexItemData(
                guid="plex://movie/source123",
                title="Source Movie",
                year=2024,
                media_type="movie",
            )
        ]
        
        result = await sync_all_users(db_session)
        
        # Verify source was created
        from app.modules.plex.models import WishlistItemSource
        sources = db_session.query(WishlistItemSource).filter(
            WishlistItemSource.plex_user_id == sample_user.id
        ).all()
        
        assert len(sources) == 1

    @pytest.mark.asyncio
    @patch("app.modules.plex.service.get_watchlist")
    async def test_sync_skips_inactive_users(
        self, mock_get_watchlist, db_session, sample_inactive_user
    ):
        """Test sync skips inactive users."""
        result = await sync_all_users(db_session)
        
        assert result["users_processed"] == 0
        mock_get_watchlist.assert_not_called()

