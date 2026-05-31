"""Extract and normalize BitTorrent infohashes from magnets and Deluge uids."""
import re

_BTIH_HEX = re.compile(r"btih:([0-9a-f]{40})", re.IGNORECASE)
_BTIH_B32 = re.compile(r"btih:([a-z2-7]{32})", re.IGNORECASE)


def normalize_infohash(value: str | None) -> str | None:
    if not value:
        return None
    cleaned = value.strip().lower()
    if len(cleaned) == 40 and all(c in "0123456789abcdef" for c in cleaned):
        return cleaned
    return None


def infohash_from_magnet(value: str | None) -> str | None:
    if not value:
        return None
    hex_match = _BTIH_HEX.search(value)
    if hex_match:
        return hex_match.group(1).lower()
    return None


def infohash_from_release(release_guid: str | None, magnet_url: str | None = None) -> str | None:
    for candidate in (release_guid, magnet_url):
        found = infohash_from_magnet(candidate)
        if found:
            return found
    return normalize_infohash(release_guid)
