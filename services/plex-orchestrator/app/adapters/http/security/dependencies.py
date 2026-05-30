"""Shared API dependencies for all microservices."""
from typing import Annotated
from fastapi import Depends

# Re-export core dependencies for microservice isolation
from app.adapters.http.security.security import get_api_key, mask_token

APIKey = Annotated[str, Depends(get_api_key)]

