"""Classify Deluge swarm connectivity for /deluge/test-connection (informational)."""
from typing import Iterable, Literal, TypedDict

TorrentConnectivity = Literal["idle", "good", "degraded", "stalled"]

ACTIVE_DOWNLOAD_STATES = frozenset(
    {"downloading", "queued", "active", "checking", "allocating"}
)


def _is_active_download_state(state: str | None) -> bool:
    return (state or "").lower() in ACTIVE_DOWNLOAD_STATES


class DelugeSwarmMetrics(TypedDict):
    torrent_connectivity: TorrentConnectivity
    dht_nodes: int | None
    has_incoming_connections: bool | None
    downloading_count: int
    active_download_count: int
    total_download_bps: int
    total_peer_count: int


class _TorrentLike(TypedDict, total=False):
    state: str
    download_payload_rate: int
    num_peers: int


def classify_torrent_connectivity(
    torrents: Iterable[_TorrentLike],
    *,
    dht_nodes: int | None = None,
    has_incoming_connections: bool | None = None,
) -> DelugeSwarmMetrics:
    """
    idle: no torrents in active download states
    good: at least one active torrent has non-zero download throughput (internet working)
    degraded: peers exist but no download throughput (likely VPN/swarm issue, not bad torrent)
    stalled: active downloads with no peers and no throughput
    """
    downloading = [
        t
        for t in torrents
        if _is_active_download_state(t.get("state"))
    ]
    total_download_bps = sum(
        int(t.get("download_payload_rate") or 0) for t in downloading
    )
    total_peer_count = sum(int(t.get("num_peers") or 0) for t in downloading)
    active_download_count = sum(
        1
        for t in downloading
        if (int(t.get("download_payload_rate") or 0) > 0)
        or (int(t.get("num_peers") or 0) > 0)
    )

    if not downloading:
        connectivity: TorrentConnectivity = "idle"
    elif total_download_bps > 0:
        connectivity = "good"
    elif total_peer_count > 0:
        connectivity = "degraded"
    else:
        connectivity = "stalled"

    return {
        "torrent_connectivity": connectivity,
        "dht_nodes": dht_nodes,
        "has_incoming_connections": has_incoming_connections,
        "downloading_count": len(downloading),
        "active_download_count": active_download_count,
        "total_download_bps": total_download_bps,
        "total_peer_count": total_peer_count,
    }


