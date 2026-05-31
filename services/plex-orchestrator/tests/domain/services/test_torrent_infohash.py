"""Tests for torrent infohash helpers."""
from app.domain.services.torrent_infohash import (
    infohash_from_magnet,
    infohash_from_release,
    normalize_infohash,
)


def test_normalize_infohash_accepts_40_char_hex():
    assert normalize_infohash("A" * 40) == "a" * 40


def test_infohash_from_magnet_url():
    infohash = "a" * 40
    magnet = f"magnet:?xt=urn:btih:{infohash.upper()}&dn=Example"
    assert infohash_from_magnet(magnet) == infohash


def test_infohash_from_release_prefers_guid():
    guid = "magnet:?xt=urn:btih:DEADBEEF00000000000000000000000000000001"
    assert infohash_from_release(guid, None) == "deadbeef00000000000000000000000000000001"
