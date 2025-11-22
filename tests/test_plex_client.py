import pytest
import respx
from fastapi import HTTPException

from app.services.plex_client import get_watchlist, normalize_watchlist_item


class TestNormalizeWatchlistItem:
    """Tests for normalize_watchlist_item function."""
    
    def test_normalize_valid_item(self):
        """Test normalizing a valid Plex API item."""
        item = {
            "guid": "plex://movie/guid/tmdb://12345",
            "title": "Test Movie",
            "year": 2023,
        }
        result = normalize_watchlist_item(item)
        
        assert result is not None
        assert result["uid"] == "plex://movie/guid/tmdb://12345"
        assert result["title"] == "Test Movie"
        assert result["year"] == 2023
    
    def test_normalize_item_with_uppercase_keys(self):
        """Test normalizing item with uppercase keys."""
        item = {
            "GUID": "plex://movie/guid/tmdb://12345",
            "Title": "Test Movie",
            "Year": 2023,
        }
        result = normalize_watchlist_item(item)
        
        assert result is not None
        assert result["uid"] == "plex://movie/guid/tmdb://12345"
        assert result["title"] == "Test Movie"
        assert result["year"] == 2023
    
    def test_normalize_item_missing_guid(self):
        """Test normalizing item without GUID."""
        item = {
            "title": "Test Movie",
            "year": 2023,
        }
        result = normalize_watchlist_item(item)
        
        assert result is None
    
    def test_normalize_item_missing_title(self):
        """Test normalizing item without title."""
        item = {
            "guid": "plex://movie/guid/tmdb://12345",
            "year": 2023,
        }
        result = normalize_watchlist_item(item)
        
        assert result is None
    
    def test_normalize_item_without_year(self):
        """Test normalizing item without year."""
        item = {
            "guid": "plex://movie/guid/tmdb://12345",
            "title": "Test Movie",
        }
        result = normalize_watchlist_item(item)
        
        assert result is not None
        assert result["year"] is None
    
    def test_normalize_item_invalid_year(self):
        """Test normalizing item with invalid year."""
        item = {
            "guid": "plex://movie/guid/tmdb://12345",
            "title": "Test Movie",
            "year": "invalid",
        }
        result = normalize_watchlist_item(item)
        
        assert result is not None
        assert result["year"] is None


@pytest.mark.asyncio
class TestGetWatchlist:
    """Tests for get_watchlist function."""
    
    @respx.mock
    async def test_get_watchlist_success(self):
        """Test successfully fetching watchlist."""
        token = "test-token-123"
        
        # Mock Plex API response
        mock_response = {
            "MediaContainer": {
                "Metadata": [
                    {
                        "guid": "plex://movie/guid/tmdb://12345",
                        "title": "Test Movie 1",
                        "year": 2023,
                    },
                    {
                        "guid": "plex://movie/guid/tmdb://67890",
                        "title": "Test Movie 2",
                        "year": 2024,
                    },
                ]
            }
        }
        
        respx.get("https://discover.provider.plex.tv/v2/watchlist").mock(
            return_value=respx.MockResponse(200, json=mock_response)
        )
        
        result = await get_watchlist(token)
        
        assert len(result) == 2
        assert result[0]["uid"] == "plex://movie/guid/tmdb://12345"
        assert result[0]["title"] == "Test Movie 1"
        assert result[1]["uid"] == "plex://movie/guid/tmdb://67890"
    
    @respx.mock
    async def test_get_watchlist_pagination(self):
        """Test fetching watchlist with pagination."""
        token = "test-token-123"
        
        # First page
        respx.get(url__regex=r"https://discover\.provider\.plex\.tv/v2/watchlist.*page=1.*").mock(
            return_value=respx.MockResponse(200, json={
                "MediaContainer": {
                    "Metadata": [
                        {"guid": f"plex://movie/guid/tmdb://{i}", "title": f"Movie {i}"}
                        for i in range(50)
                    ]
                }
            })
        )
        
        # Second page (smaller, indicating last page)
        respx.get(url__regex=r"https://discover\.provider\.plex\.tv/v2/watchlist.*page=2.*").mock(
            return_value=respx.MockResponse(200, json={
                "MediaContainer": {
                    "Metadata": [
                        {"guid": "plex://movie/guid/tmdb://50", "title": "Movie 50"}
                    ]
                }
            })
        )
        
        result = await get_watchlist(token)
        
        assert len(result) == 51
    
    @respx.mock
    async def test_get_watchlist_invalid_token(self):
        """Test fetching watchlist with invalid token."""
        token = "invalid-token"
        
        respx.get("https://discover.provider.plex.tv/v2/watchlist").mock(
            return_value=respx.MockResponse(401)
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await get_watchlist(token)
        
        assert exc_info.value.status_code == 401
    
    @respx.mock
    async def test_get_watchlist_rate_limit(self):
        """Test handling rate limiting."""
        token = "test-token-123"
        
        respx.get("https://discover.provider.plex.tv/v2/watchlist").mock(
            return_value=respx.MockResponse(429)
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await get_watchlist(token)
        
        assert exc_info.value.status_code == 429
    
    @respx.mock
    async def test_get_watchlist_empty(self):
        """Test fetching empty watchlist."""
        token = "test-token-123"
        
        respx.get("https://discover.provider.plex.tv/v2/watchlist").mock(
            return_value=respx.MockResponse(200, json={"MediaContainer": {"Metadata": []}})
        )
        
        result = await get_watchlist(token)
        
        assert len(result) == 0
    
    @respx.mock
    async def test_get_watchlist_server_error(self):
        """Test handling server errors."""
        token = "test-token-123"
        
        respx.get("https://discover.provider.plex.tv/v2/watchlist").mock(
            return_value=respx.MockResponse(500)
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await get_watchlist(token)
        
        assert exc_info.value.status_code == 502

