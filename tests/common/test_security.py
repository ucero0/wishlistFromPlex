"""Tests for security utilities."""
import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException

from app.core.security import mask_token, verify_api_key, get_api_key


class TestMaskToken:
    """Tests for mask_token function."""

    def test_mask_normal_token(self):
        """Test masking a normal length token."""
        token = "abcdefghijklmnop"
        masked = mask_token(token)
        assert masked == "abcd****mnop"

    def test_mask_short_token(self):
        """Test masking a short token."""
        token = "short"
        masked = mask_token(token)
        assert masked == "****"

    def test_mask_empty_token(self):
        """Test masking an empty token."""
        token = ""
        masked = mask_token(token)
        assert masked == "****"

    def test_mask_none_token(self):
        """Test masking a None token."""
        masked = mask_token(None)
        assert masked == "****"

    def test_mask_exact_8_chars(self):
        """Test masking a token with exactly 8 characters."""
        token = "12345678"
        masked = mask_token(token)
        assert masked == "1234****5678"

    def test_mask_preserves_first_and_last_4(self):
        """Test that masking preserves first 4 and last 4 characters."""
        token = "ABCD-secret-data-WXYZ"
        masked = mask_token(token)
        assert masked.startswith("ABCD")
        assert masked.endswith("WXYZ")
        assert "****" in masked


class TestVerifyApiKey:
    """Tests for verify_api_key function."""

    def test_verify_valid_key(self):
        """Test verifying a valid API key."""
        # The test environment sets API_KEY to "test-api-key-12345"
        result = verify_api_key("test-api-key-12345")
        assert result is True

    def test_verify_invalid_key(self):
        """Test verifying an invalid API key."""
        result = verify_api_key("wrong-key")
        assert result is False

    def test_verify_empty_key(self):
        """Test verifying an empty API key."""
        result = verify_api_key("")
        assert result is False

    def test_verify_none_key(self):
        """Test verifying a None API key."""
        result = verify_api_key(None)
        assert result is False


class TestGetApiKey:
    """Tests for get_api_key dependency."""

    def test_get_api_key_valid(self):
        """Test get_api_key with valid key."""
        result = get_api_key("test-api-key-12345")
        assert result == "test-api-key-12345"

    def test_get_api_key_invalid(self):
        """Test get_api_key with invalid key raises HTTPException."""
        with pytest.raises(HTTPException) as exc_info:
            get_api_key("wrong-key")
        
        assert exc_info.value.status_code == 401
        assert "Invalid or missing API key" in exc_info.value.detail

    def test_get_api_key_missing(self):
        """Test get_api_key with missing key raises HTTPException."""
        with pytest.raises(HTTPException) as exc_info:
            get_api_key(None)
        
        assert exc_info.value.status_code == 401

    def test_get_api_key_empty(self):
        """Test get_api_key with empty key raises HTTPException."""
        with pytest.raises(HTTPException) as exc_info:
            get_api_key("")
        
        assert exc_info.value.status_code == 401

