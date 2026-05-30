"""Tests for Deluge route helpers."""
import pytest

from app.adapters.http.routes.deluge.helpers import (
    DETAIL_NO_DOWNLOADING_TORRENTS,
    ensure_torrents_found,
    to_torrent_response,
)
from app.domain.models.torrent import Torrent


def test_ensure_torrents_found_raises_404_when_empty():
    with pytest.raises(Exception) as exc_info:
        ensure_torrents_found([], detail=DETAIL_NO_DOWNLOADING_TORRENTS)
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == DETAIL_NO_DOWNLOADING_TORRENTS


def test_to_torrent_response_allows_null_eta_and_size():
    t = Torrent(
        hash="a" * 40,
        file_name="movie.mkv",
        state="Downloading",
        progress=5.0,
        eta=None,
        total_size=None,
    )
    resp = to_torrent_response(t)
    assert resp.eta is None
    assert resp.total_size is None
