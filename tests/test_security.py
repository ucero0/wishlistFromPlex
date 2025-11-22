import pytest
from fastapi import HTTPException

from app.core.security import mask_token, verify_api_key, get_api_key
from app.core.config import settings


class TestMaskToken:
    """Tests for token masking function."""
    
    def test_mask_token_normal(self):
        """Test masking a normal token."""
        token = "plex_token_abcdefghijklmnop1234567890"
        masked = mask_token(token)
        assert masked.startswith("plex")
        assert masked.endswith("7890")
        assert "****" in masked
        assert len(masked) < len(token)
    
    def test_mask_token_short(self):
        """Test masking a short token."""
        token = "short"
        masked = mask_token(token)
        assert masked == "****"
    
    def test_mask_token_empty(self):
        """Test masking an empty token."""
        masked = mask_token("")
        assert masked == "****"
    
    def test_mask_token_none(self):
        """Test masking None token."""
        masked = mask_token(None)
        assert masked == "****"


class TestVerifyApiKey:
    """Tests for API key verification."""
    
    def test_verify_api_key_valid(self, test_settings):
        """Test verifying a valid API key."""
        # Temporarily override settings
        original_key = settings.api_key
        settings.api_key = "test-key-123"
        
        assert verify_api_key("test-key-123") is True
        
        # Restore
        settings.api_key = original_key
    
    def test_verify_api_key_invalid(self, test_settings):
        """Test verifying an invalid API key."""
        original_key = settings.api_key
        settings.api_key = "test-key-123"
        
        assert verify_api_key("wrong-key") is False
        assert verify_api_key(None) is False
        
        settings.api_key = original_key


class TestGetApiKey:
    """Tests for API key dependency."""
    
    def test_get_api_key_valid(self, test_settings):
        """Test getting API key with valid key."""
        from unittest.mock import patch
        from app.core import security
        
        with patch.object(security.settings, 'api_key', 'test-key-123'):
            # This is a dependency function, so we test it directly
            result = get_api_key("test-key-123")
            assert result == "test-key-123"
    
    def test_get_api_key_missing(self, test_settings):
        """Test getting API key with missing key."""
        from unittest.mock import patch
        from app.core import security
        
        with patch.object(security.settings, 'api_key', 'test-key-123'):
            with pytest.raises(HTTPException) as exc_info:
                get_api_key(None)
            
            assert exc_info.value.status_code == 401
    
    def test_get_api_key_invalid(self, test_settings):
        """Test getting API key with invalid key."""
        from unittest.mock import patch
        from app.core import security
        
        with patch.object(security.settings, 'api_key', 'test-key-123'):
            with pytest.raises(HTTPException) as exc_info:
                get_api_key("wrong-key")
            
            assert exc_info.value.status_code == 401

