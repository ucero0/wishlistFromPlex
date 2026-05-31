import base64
import json

from app.infrastructure.external_apis.tmdb.jwt_utils import account_object_id_from_access_token


def _token(sub: str) -> str:
    header = base64.urlsafe_b64encode(b'{"alg":"HS256","typ":"JWT"}').decode().rstrip("=")
    payload = (
        base64.urlsafe_b64encode(json.dumps({"sub": sub}).encode()).decode().rstrip("=")
    )
    return f"{header}.{payload}.signature"


def test_account_object_id_from_access_token_returns_sub():
    assert account_object_id_from_access_token(_token("691f363df62a7a034fa2ba")) == (
        "691f363df62a7a034fa2ba"
    )


def test_account_object_id_from_access_token_invalid_token():
    assert account_object_id_from_access_token("not-a-jwt") is None
