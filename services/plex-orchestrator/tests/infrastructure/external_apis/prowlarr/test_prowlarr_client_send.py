"""Tests for Prowlarr send_to_download_client idempotency."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.infrastructure.external_apis.prowlarr.prowlarr_client import (
    ProwlarrClient,
    is_deluge_torrent_already_in_session,
    is_prowlarr_deluge_send_recoverable,
)


def test_is_deluge_torrent_already_in_session_detects_deluge_error():
    body = (
        '{"message": "Failure: AddTorrentError: Torrent already in session '
        '(2b49afde991e83dce8f4b2ef5fff5c05)"}'
    )
    assert is_deluge_torrent_already_in_session(body) is True


def test_is_deluge_torrent_already_in_session_false_for_other_errors():
    assert is_deluge_torrent_already_in_session('{"message": "Indexer down"}') is False


def test_is_prowlarr_deluge_send_recoverable_unknown_method():
    body = "DownloadClientAuthenticationException: Unknown method at DelugeProxy.SetLabel"
    assert is_prowlarr_deluge_send_recoverable(body) is True


@pytest.mark.asyncio
async def test_send_to_download_client_treats_unknown_method_as_success():
    client = ProwlarrClient()
    response = MagicMock()
    response.status_code = 500
    response.text = "Unknown method DelugeProxy"

    mock_http = AsyncMock()
    mock_http.post = AsyncMock(return_value=response)
    mock_http.__aenter__ = AsyncMock(return_value=mock_http)
    mock_http.__aexit__ = AsyncMock(return_value=None)

    with patch("app.infrastructure.external_apis.prowlarr.prowlarr_client.httpx.AsyncClient", return_value=mock_http):
        ok = await client.send_to_download_client("guid-1", 1)

    assert ok is True


@pytest.mark.asyncio
async def test_send_to_download_client_treats_duplicate_deluge_add_as_success():
    client = ProwlarrClient()
    response = MagicMock()
    response.status_code = 500
    response.text = (
        "Torrent already in session (2b49afde991e83dce8f4b2ef5fff5c05)"
    )

    mock_http = AsyncMock()
    mock_http.post = AsyncMock(return_value=response)
    mock_http.__aenter__ = AsyncMock(return_value=mock_http)
    mock_http.__aexit__ = AsyncMock(return_value=None)

    with patch("app.infrastructure.external_apis.prowlarr.prowlarr_client.httpx.AsyncClient", return_value=mock_http):
        ok = await client.send_to_download_client("guid-1", 1)

    assert ok is True
