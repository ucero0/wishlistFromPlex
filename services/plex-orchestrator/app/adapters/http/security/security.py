from fastapi import Header, HTTPException, status
from typing import Optional
from app.core.config import settings
from fastapi.security import APIKeyHeader
from fastapi import Security

API_KEY_NAME = "X-API-Key"

api_key_header = APIKeyHeader(
    name=API_KEY_NAME,
    auto_error=False,
)
def mask_token(token: str) -> str:
    """Returns a masked version of the token for display purposes."""
    if not token or len(token) < 8:
        return "****"
    return f"{token[:4]}****{token[-4:]}"


def verify_api_key(api_key: Optional[str] = None) -> bool:
    """Verify that the provided API key matches the configured key."""
    if not api_key:
        return False
    return api_key == settings.api_key


def get_api_key(x_api_key: Optional[str] = Security(api_key_header)) -> str:
    """FastAPI dependency to verify API key from header."""
    if not x_api_key or not verify_api_key(x_api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key. Provide X-API-Key header.",
        )
    return x_api_key



