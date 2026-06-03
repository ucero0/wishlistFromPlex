"""Tests for Deluge swarm stats (informational only, not VPN health)."""
from app.domain.services.deluge_swarm_health import classify_torrent_connectivity


def test_idle_when_no_active_downloads():
    metrics = classify_torrent_connectivity(
        [{"state": "Seeding", "download_payload_rate": 1000, "num_peers": 3}],
    )
    assert metrics["torrent_connectivity"] == "idle"


def test_good_when_downloading():
    metrics = classify_torrent_connectivity(
        [{"state": "Downloading", "download_payload_rate": 512000, "num_peers": 0}]
    )
    assert metrics["torrent_connectivity"] == "good"


def test_degraded_when_peers_but_no_throughput():
    metrics = classify_torrent_connectivity(
        [{"state": "Downloading", "download_payload_rate": 0, "num_peers": 2}]
    )
    assert metrics["torrent_connectivity"] == "degraded"


def test_stalled_when_no_peers_or_traffic():
    metrics = classify_torrent_connectivity(
        [
            {"state": "Downloading", "download_payload_rate": 0, "num_peers": 0},
            {"state": "Queued", "download_payload_rate": 0, "num_peers": 0},
        ],
    )
    assert metrics["torrent_connectivity"] == "stalled"
