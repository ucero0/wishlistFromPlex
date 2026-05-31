"""Parse TMDB v4 access token claims."""
import base64
import json


def account_object_id_from_access_token(access_token: str) -> str | None:
    """Return TMDB v4 account object id from the token ``sub`` claim."""
    parts = access_token.split(".")
    if len(parts) < 2:
        return None
    payload = parts[1]
    padding = "=" * (-len(payload) % 4)
    try:
        data = json.loads(base64.urlsafe_b64decode(payload + padding))
    except (ValueError, json.JSONDecodeError):
        return None
    sub = data.get("sub")
    return str(sub) if sub else None
